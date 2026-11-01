[English](README.md)

# Kai_ai-passport-suite

基于 [KevinCJM/ai-passport-all-in-one](https://github.com/KevinCJM/ai-passport-all-in-one) 的个人 fork，同时维护 AI Passport 设备固件和 macOS 助手。

本版本把百度热榜替换为 AIHOT 的 AI 热点 Top 10。设备通过 Wi-Fi 获取榜单，打开详情后再读取有限长度的事件摘要。同时保留本机已测试的助手修复：识别改名后的蓝牙设备、语音输入退出再进入时复用通道，以及修正连接状态误报。

- [AIHOT 行为与数据约定](docs/aihot.zh_CN.md)
- [构建与安装](docs/local-development.zh_CN.md)
- [实现与验证交接](HANDOFF.zh_CN.md)
- [上游应用说明](.github/README.md)

## 开始

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
source tools/activate-local.sh
./tools/validate.sh
```

固件使用 **ESP-IDF 6.1**、ESP32-C3、8 MB Flash、无 PSRAM。可以与已有 ESP-IDF 5.5.3 并存。分区布局和持久数据偏移保持上游版本的设置；构建通过不能代替实机验收。

已安装的 Mac 助手把配对数据保存在 `~/Library/Application Support/AI Passport/`，仓库不包含配对凭据或本机签名密钥。固件修改需要单独授权后刷机；日常 AIHOT 内容刷新无需重新刷机。

代码使用 MIT 许可，保留上游署名。AIHOT 内容来自 [aihot.news](https://aihot.news/)，遵循其[公开使用规则](https://aihot.news/agent?tab=api)。
