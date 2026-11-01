[English](local-development.md)

# 本地开发

个人仓库为 `trojanwk/Kai_ai-passport-suite`，上游为 `KevinCJM/ai-passport-all-in-one`，当前工作分支是 `codex/aihot-news`。原有开发板模板是另一个项目，其 ESP-IDF 5.5.3 环境不用于本应用。

## 环境

安装 Python 3.12、uv、Xcode 命令行工具和 Homebrew `libslirp`（现有 macOS PPP 辅助程序需要），然后创建项目环境：

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
```

把官方 ESP-IDF **v6.1** 标签克隆到 `~/esp/esp-idf-v6.1`，初始化子模块，再通过其 `tools/idf_tools.py` 安装 ESP32-C3 工具和 Python 环境。已有 SDK 可用 `AI_PASSPORT_IDF_ROOT` 指定。构建前执行 `source tools/activate-local.sh`，选择匹配的 IDF Python 环境；只影响当前 shell，不替换其他 SDK。

```bash
source tools/activate-local.sh
idf.py --version
bash scripts/fetch_deps.sh
./tools/validate.sh
```

完整检查依次执行所有主机测试、路由校验、设备固件构建和校验打包。开发中可以单独运行 `.venv/bin/python tests/test_passport_aihot.py -v` 或 `bash scripts/build_passport_suite.sh device`。字体生成器使用本项目安装的 Pillow。新增中文文案还须检查字形覆盖；设备实际显示仍需独立验收。

## 产物与安装

`tools/package_firmware.py` 生成被 Git 忽略的 `releases/Kai_ai-passport-suite-<版本>-<应用哈希>/` 文件夹和 ZIP。清单记录源码提交、未提交状态、完整分区布局、镜像哈希和 ELF 身份。配套 ELF/MAP 保存在被忽略的 `build/firmware/<应用 SHA256>/`，用于分析崩溃，不得替换为其他构建的 ELF。

安装参见随包附带的[刷机说明](flash-guide.zh_CN.md)。兼容设备经明确授权后，可通过本地浏览器页面只更新应用。合并镜像的数据影响不同，不应用于保留设置的更新。

已安装的电脑助手位于 `~/Applications/AI Passport Assistant.app`。配对配置和本地签名身份位于仓库之外的 `~/Library/Application Support/AI Passport/`，不得提交这些文件或私有诊断日志。构建固件不会重新安装电脑助手。

## 验证边界

主机测试包含真实 C++ 有界 AIHOT 解析器的 AddressSanitizer/UndefinedBehaviorSanitizer 检查，以及助手蓝牙回归测试。真实 API 检查只证明响应兼容，不能替代设备 TLS、内存峰值、界面、按键和音频验收。经授权刷机后，在设备上逐项验收并回写交接记录。
