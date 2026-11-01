#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
PROJECT="$ROOT/firmware/passport_suite"
if [[ "${1:-}" == connectivity ]]; then PROJECT="$ROOT/firmware/passport_connectivity"; fi
if [[ "${1:-}" == device ]]; then PROJECT="$ROOT/firmware/passport_device"; fi
# Honor the caller's activated SDK; otherwise use this fork's local activation helper.
if [[ -z "${IDF_PATH:-}" ]]; then source "$ROOT/tools/activate-local.sh"; fi
idf_version="$(python "$IDF_PATH/tools/idf.py" --version)"
[[ "$idf_version" =~ ^ESP-IDF\ v6\.1([.-]|$) ]] || { echo "ESP-IDF 6.1 is required; found $idf_version" >&2; exit 1; }
# Every component is local (components/, deps/): no registry lookups.
export IDF_COMPONENT_CHECK_NEW_VERSION=0 IDF_COMPONENT_MANAGER=0
[[ -n "${IDF_PATH:-}" ]] || { echo "ESP-IDF 6.1 not found: source its export.sh first" >&2; exit 1; }
[[ -d "$ROOT/deps/lvgl__lvgl" ]] || bash "$ROOT/scripts/fetch_deps.sh"

if [[ "${1:-}" == connectivity || "${1:-}" == device ]]; then
  HELPER="$ROOT/experiments/passport-connectivity-tools/bin/passport-dictation"
  mkdir -p "${HELPER%/*}"
  if [[ -f "$ROOT/scripts/mac_dictation_bridge.cpp" && ( ! -x "$HELPER" || "$ROOT/scripts/mac_dictation_bridge.cpp" -nt "$HELPER" ) ]]; then
    /usr/bin/clang++ -std=c++20 "$ROOT/scripts/mac_dictation_bridge.cpp" -framework CoreFoundation -framework ApplicationServices -o "$HELPER"
  fi
  PPP_HELPER="$ROOT/experiments/passport-connectivity-tools/bin/passport-ppp"
  if [[ -f "$ROOT/scripts/passport_ppp_gateway.cpp" && ( ! -x "$PPP_HELPER" || "$ROOT/scripts/passport_ppp_gateway.cpp" -nt "$PPP_HELPER" ) ]]; then
    /usr/bin/clang++ -std=c++20 -Wall -Wextra "$ROOT/scripts/passport_ppp_gateway.cpp" -I/opt/homebrew/include -L/opt/homebrew/lib -lslirp -o "$PPP_HELPER"
  fi
fi

cd "$PROJECT"
FONT_PYTHON="$ROOT/.venv/bin/python"
[[ -x "$FONT_PYTHON" ]] || FONT_PYTHON=python3
# The generated fonts are committed: without Pillow the build uses them as they are.
if "$FONT_PYTHON" -c "import PIL" 2>/dev/null; then "$FONT_PYTHON" "$ROOT/scripts/generate_passport_font.py"; else echo "Pillow missing: using the committed fonts"; fi
python "$IDF_PATH/tools/idf.py" -DIDF_TARGET=esp32c3 build
python "$IDF_PATH/tools/idf.py" merge-bin -o merged_flash.bin
# 语音唤醒's model, written by flash_passport_device.py to the free flash after the identity card.
if [[ -d components/espressif__esp-sr ]]; then python -I components/espressif__esp-sr/model/pack_model.py -m components/espressif__esp-sr/model/wakenet_model -o "$PWD/build/srmodels.bin" >/dev/null; fi
python - <<'PY'
import json
from pathlib import Path
c = json.loads(Path('build/config/sdkconfig.json').read_text())
assert c['IDF_TARGET'] == 'esp32c3'
assert c['ESPTOOLPY_FLASHSIZE'] == '8MB' and not c.get('SPIRAM')
assert c['ESP_WIFI_ENABLED']
assert not c.get('COMPILER_CXX_EXCEPTIONS') and not c.get('COMPILER_CXX_RTTI')
name = json.loads(Path('build/project_description.json').read_text())['project_name']
assert Path('build', name + '.bin').stat().st_size <= (0x400000 if name=='passport_device' else 0x340000)
print('SUITE_BUILD_OK C++ C3 8MB PSRAM=0 physical_build='+str(name=='passport_device'))
PY
