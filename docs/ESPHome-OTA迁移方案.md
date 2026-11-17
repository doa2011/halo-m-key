# ESPHome OTA 切换到 CC2530 Flasher

## 当前设备配置

根据用户提供的 `20261010.yaml`：
- `esp32.board: esp32dev`
- Arduino framework
- 原生 ESPHome OTA，使用加密 key
- YAML 未声明自定义分区表；实际构建分区仍需从当前 ESPHome build 目录确认

## 目标镜像与构建

GitHub Actions 从固定上游提交构建经典 ESP32 `esp32dev` 固件，目标 app-only 文件为 `cc2530-flasher-esp32dev-app.bin`。它不是 ESP32-S3 镜像，也不是包含 bootloader/partition table 的 factory 镜像。

当前 PlatformIO 配置采用 Arduino ESP32 `default.csv` 双 OTA app slot，每个 slot 为 `0x140000`（1,310,720 bytes）。CI 会检查 app image 头部及大小。**这只是构建端预检；真正上传前必须核对当前 ESPHome 实际分区表与 OTA slot 大小。**

## 一次性迁移步骤

1. 在 Home Assistant / ESPHome 当前构建环境中，备份 YAML、secrets（离线保管）、当前 app 镜像和分区表。
2. 从 GitHub Actions 下载 `cc2530-flasher-esp32dev-app.bin` 与 `BUILD-MANIFEST.txt`。
3. 核对设备确实为经典 ESP32，实际 Flash/分区表与本次构建的 `default.csv` 兼容，inactive OTA slot 至少容纳 BIN。
4. 确认稳定供电，并准备 USB-UART 串口恢复。
5. 使用当前 ESPHome 版本的 CLI 和现有加密 key 上传 app-only 镜像，例如：

```bash
esphome upload --file cc2530-flasher-esp32dev-app.bin --device <ESP32当前IP> --prompt-ota-key
```

按提示输入现有 OTA 加密 key。**不能上传 factory image，也不要更新 bootloader 或 partition table。**

上传成功后，ESPHome API/OTA 与 HA 实体将消失，设备切换为 CC Flasher。原 ESPHome OTA 不再可用；如果新固件启动失败，只能通过 USB-UART 恢复。

## 后续 OTA

新固件加入 ArduinoOTA，主机名 `cc-tool.local`，初始密码 `12345678`。进入网页后可在 ESP32 OTA Password 区域修改密码。修改后同步更新 `firmware/esp32/platformio.ini` 中的 `upload_flags`。

```bash
pio run -e esp32dev -t upload
```

GitHub Actions 自动构建并保留 30 天 artifact；推送 `v*` 标签时发布 Release。CI artifact 不能替代设备端实测。

## GPIO

| ESP32 GPIO | 分配 | 状态 |
|---|---|---|
| 18 | CC DC | 临时分配，实物接线前确认 |
| 19 | CC DD | 临时分配，实物接线前确认 |
| 21 | CC RESET_N | 临时分配，实物接线前确认 |
| 16 / D16 | 保留 | 不分配、不配置 |
| 17 / D17 | 保留 | 不分配、不配置 |

18/19/21 在原净水器 YAML 中分别用于 TDS UART/I²C；临时转换后不再运行原净水器配置，因此释放出来。仍须核实 MOS_X4 板级引出及板载电路。

## 参考资料

- ESPHome CLI 预编译镜像上传：https://esphome.io/guides/cli/#uploading-a-prebuilt-image-without-a-configuration
- ESPHome 原生 OTA：https://esphome.io/components/ota/esphome/
- ESP-IDF OTA 分区机制：https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html
