# ESP32_MOS_X4 临时烧录器

## 目标与引脚

目标板是当前运行 ESPHome、`board: esp32dev` 的 ESP32_MOS_X4。此次临时转换后不再承担 RO 净水器控制。

| ESP32 GPIO | CC2530 |
|---|---|
| GPIO18 | DC / P2.2（QFN40 pin 34） |
| GPIO19 | DD / P2.1（QFN40 pin 35） |
| GPIO21 | RESET_N（QFN40 pin 20） |

**GPIO16/D16 与 GPIO17/D17 严格保留，不在代码中配置或使用。** 18/19/21 是因临时停用 TDS UART 与 I²C 后重新分配的信号脚，仍需在 MOS_X4 实物上确认引出和无板载冲突。

## 构建

- 上游：[z9m/ESP32-CC-Tool-Pro](https://github.com/z9m/ESP32-CC-Tool-Pro)
- 固定提交：`3a5b9fc123cf660a61edad1d79502ea7b36c05fb`
- PlatformIO 目标：`esp32dev`（经典 ESP32），不再使用上游默认 ESP32-S3
- 适配脚本：`tools/prepare_esp32_flasher.py`
- 构建配置：本目录 `platformio.ini`
- 自动构建：`.github/workflows/esp32-flasher-build.yml`

GitHub Actions push/PR 时构建并上传 artifact。推送版本标签（如 `v0.1.0`）时创建 Release。发布包包括 app-only BIN、SHA256、manifest 与对应 GPL 源码。

## OTA

首次迁移仍使用当前 ESPHome 原生加密 OTA；目标镜像必须是 app-only image，不能使用 factory image。构建检查以标准 `default.csv` 双 OTA 分区（每个 app slot 0x140000）为上限，但在上传前还必须确认当前 ESPHome 设备实际分区表相同。

切换后固件提供 ArduinoOTA：
- mDNS 主机名：`cc-tool.local`
- 初始 OTA 密码：`12345678`
- 网页 WiFi Settings 下方可设置新 OTA 密码
- PlatformIO 默认上传命令：`pio run -e esp32dev -t upload`

更改 OTA 密码后，请同步修改本文件夹 `platformio.ini` 的 `upload_flags`。不要在不可信网络中保留初始密码。

## 恢复

切换后 ESPHome API/OTA 不再运行，不能再用原 ESPHome OTA 回刷。请保留原 YAML、secrets（离线保管）和串口恢复路径。首次迁移前确认 USB-UART 可以进入下载模式。

## 安全边界

- 不接 5V 到 CC2530 VDD 或 DC/DD/RESET。
- ESP32 与 CC2530 共地。
- 目标板电源只允许一个受控 3.3V 来源，避免纽扣电池与外部电源反灌。
- 备份 Halo 原厂 Flash 前，不执行 Erase / Unlock / Write。
