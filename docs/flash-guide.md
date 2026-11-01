[简体中文](flash-guide.zh_CN.md)

# Install the AIHOT Firmware

Version: **0.5.21-aihot.1**, for AI Passport ESP32-C3, 8 MB Flash, no PSRAM. The firmware replaces Baidu trends with AIHOT and preserves the upstream partition definitions. Creating this package does not flash a device.

## Application update

First verify that the device already uses the matching partition table in `manifest.json`: one 4 MB factory application at `0x10000`, legacy NVS at `0x9000`, card data at `0x410000`, storage at `0x420000`, and application NVS at `0x620000`. The same hardware model or a successful USB connection is not proof of matching partitions.

After approving the exact firmware and its data impact, the application-only plan writes `passport_device.bin` at `0x10000`. It does not write a partition table, bootloader, NVS, identity, storage, or wake-word model, and does not request a chip erase. Existing data is preserved only if the installed layout and data formats are compatible.

For browser installation, extract the package and run a local server in its folder:

```bash
python3 -m http.server 8769 --bind 127.0.0.1
```

Open `http://localhost:8769/` in desktop Chrome or Edge. Pause the Mac companion before selecting the USB device. Review the compatibility statement and approve the application update. **Leave “Erase device” unchecked** in ESP Web Tools. The browser component is pinned to version 10.1.1 and loaded from unpkg; it requires internet access. The firmware itself is served locally. The manifest requests an explicit erase choice because ESP Web Tools otherwise defaults to erasing unknown firmware.

The equivalent approved CLI update is:

```bash
python -m esptool --chip esp32c3 -p PORT -b 921600 write-flash \
  --flash-mode keep --flash-freq keep --flash-size keep \
  0x10000 passport_device.bin
```

Replace `PORT` only with the confirmed target device. Device detection alone is not consent to flash.

## First installation or another installed layout

Do not use the application-update button until compatibility is established. `manifest.json` records the upstream first-install segments separately: bootloader at `0x0`, partition table at `0x8000`, application at `0x10000`, and the wake-word model at `0x670000` when included. Changing the partition table or application data format requires an additional data-impact review.

`merged_flash.bin` is a full image for `0x0`, not an application update. Its filled gaps can overwrite legacy NVS. Do not use it when preserving current settings. No full-chip erase is part of this package's update plan.

After an approved installation, verify startup, Chinese text, AIHOT loading, detail navigation, failed-network behavior, and the existing voice-input/companion workflow. A valid image or successful write is not proof that those behaviors pass.
