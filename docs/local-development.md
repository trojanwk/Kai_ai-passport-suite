[简体中文](local-development.zh_CN.md)

# Local Development

The personal fork is `trojanwk/Kai_ai-passport-suite`, with upstream `KevinCJM/ai-passport-all-in-one`. Work is on `codex/aihot-news`. The original board-template checkout is a separate project; its ESP-IDF 5.5.3 environment is not used by this application.

## Environment

Install Python 3.12, uv, Xcode command-line tools, and Homebrew `libslirp` (for the existing macOS PPP helper). Create the project environment:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
```

Clone the official ESP-IDF **v6.1** tag to `~/esp/esp-idf-v6.1`, initialize its submodules, then install its ESP32-C3 tools and Python environment with `tools/idf_tools.py`. An existing SDK can be selected with `AI_PASSPORT_IDF_ROOT`. Source `tools/activate-local.sh` before building; it selects the matching IDF Python environment and changes only the current shell. This does not replace other installed SDKs.

```bash
source tools/activate-local.sh
idf.py --version
bash scripts/fetch_deps.sh
./tools/validate.sh
```

The complete gate runs all host tests, routing validation, the device build and verified packaging. For iteration, run `.venv/bin/python tests/test_passport_aihot.py -v` or `bash scripts/build_passport_suite.sh device`. The font generator uses the project's Pillow installation. Chinese glyph coverage must also be checked when introducing new UI text; physical rendering remains a separate acceptance check.

## Artifacts and installation

`tools/package_firmware.py` produces an ignored `releases/Kai_ai-passport-suite-<version>-<app-hash>/` folder and ZIP. Its manifest records the source commit, dirty status, complete partition layout, image hashes, and ELF identity. Matching ELF/MAP files stay under ignored `build/firmware/<app-sha256>/`. Keep those files for crash analysis; do not substitute another build's ELF.

Use the included [flash guide](flash-guide.md). A compatible device can receive an application-only update through the local browser page, after explicit approval. The merged image has a different data impact and must not be used as a settings-preserving update.

The installed companion is `~/Applications/AI Passport Assistant.app`. Its pairing configuration and local signing identity are outside this repository under `~/Library/Application Support/AI Passport/`. Do not commit those files or private diagnostic logs. Firmware building does not reinstall the Mac companion.

## Validation boundaries

Host tests include the real bounded C++ AIHOT reader under AddressSanitizer/UndefinedBehaviorSanitizer and the companion's Bluetooth regressions. Live API checks verify response compatibility, not device TLS, memory peaks, display layout, buttons, or audio. After an approved flash, accept those behaviors on the device and record results in the handoff.
