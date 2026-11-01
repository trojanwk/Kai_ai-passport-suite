[简体中文](README.zh_CN.md)

# Kai_ai-passport-suite

Personal fork of [KevinCJM/ai-passport-all-in-one](https://github.com/KevinCJM/ai-passport-all-in-one), combining the AI Passport device firmware and macOS companion.

This fork replaces Baidu trends with AIHOT's Top 10 AI events. The device fetches the board over Wi-Fi and loads a bounded event summary when a detail is opened. It also retains the locally tested companion fixes for renamed Bluetooth devices, dictation reentry, and connection-status reporting.

- [AIHOT behavior and data contract](docs/aihot.md)
- [Build and installation](docs/local-development.md)
- [Implementation and validation checkpoint](HANDOFF.md)
- [Upstream application guide](.github/README.md)

## Start

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
source tools/activate-local.sh
./tools/validate.sh
```

The firmware uses **ESP-IDF 6.1**, ESP32-C3, 8 MB Flash, and no PSRAM. Existing ESP-IDF 5.5.3 installations can coexist. The device's partition layout and persistent-data offsets are unchanged from upstream. Build output is not evidence of physical-device acceptance.

The currently installed Mac companion keeps its pairing data under `~/Library/Application Support/AI Passport/`; no pairing credentials or local signing keys belong in this repository. Firmware changes require a separate approved flash. Daily AIHOT content refreshes do not require reflashing.

MIT code license; upstream attribution is retained. AIHOT content is provided by [aihot.news](https://aihot.news/), under its [public-use rules](https://aihot.news/agent?tab=api).
