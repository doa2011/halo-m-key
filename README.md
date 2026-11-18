# Halo M-Key (CC2530) 低功耗固件移植

> **状态：Halo 六键硬件映射已实测；ESP32_MOS_X4 的经典 ESP32 烧录器已完成 esptool 完整镜像构建配置，等待新一轮 CI 和实机串口刷写验证。Halo Zigbee HEX 尚未完成。**

## 已确认的 Halo V0.6 硬件

| 按键 | CC2530 QFN40 脚 | GPIO | 有效电平 |
|---|---:|---|---|
| S1 | 8 | P1.2 | LOW |
| S2 | 7 | P1.3 | LOW |
| S3 | 6 | P1.4 | LOW |
| S4 | 5 | P1.5 | LOW |
| S5 | 38 | P1.6 | LOW |
| S6 | 37 | P1.7 | LOW |

按键按下接 GND，当前不配置 LED。详见 `hardware/pins.csv`。

## ESP32_MOS_X4 临时烧录器

本次采用 USB-UART + Espressif esptool 首次烧录，不再依赖 ESPHome OTA。ESP32_MOS_X4 临时停止净水器 ESPHome 控制，改为运行 CC2530 Flasher。

| ESP32 GPIO | CC2530 信号 |
|---|---|
| GPIO18 | DC / P2.2 |
| GPIO19 | DD / P2.1 |
| GPIO21 | RESET_N |
| GND | GND |

GPIO16/D16、GPIO17/D17 明确保留，不分配、不配置。18/19/21 仍须按 MOS_X4 实物确认引出和板载电路后接线。

## esptool 完整烧录包

GitHub Actions 固定使用上游提交 `3a5b9fc123cf660a61edad1d79502ea7b36c05fb`，编译经典 ESP32 `esp32dev`，并将 Bootloader、Partition Table、OTA Data 初始化镜像和应用程序合并为：

`cc2530-flasher-esp32dev-factory.bin`

构建采用明确的 4 MB 分区表：两个 0x140000 OTA app slot，以及约 1.4 MB 的 LittleFS/SPIFFS 数据区，供烧录器保存 CC2530 dump 和待写入固件。实际表见 `firmware/esp32/partitions.csv`。

### Windows 串口烧录

1. 下载 GitHub Actions 的 `cc2530-flasher-esp32dev-esptool` artifact 并解压。
2. 安装 Python esptool：`py -m pip install esptool==4.9.0`。
3. 先运行 `backup_esptool.bat COMx`，对原有 4 MB Flash 连续读取两次并进行逐字节比较；只有两份备份一致才继续。
4. 确认 ESP32 芯片和 4 MB Flash，保存好双份备份。
5. 运行 `flash_esptool.bat COMx`，将 COMx 换成实际串口，例如 COM5。

脚本会先执行 `erase_flash`，再将 factory 镜像写入 0x0。**这会清空原 ESPHome 固件、分区表、Wi-Fi 凭据、NVS 和其他 Flash 数据。必须先备份，且准备好 USB-UART 恢复。**

也可以手动执行：

```powershell
py -m esptool --chip esp32 --port COM5 --baud 460800 erase_flash
py -m esptool --chip esp32 --port COM5 --baud 460800 write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB 0x0 cc2530-flasher-esp32dev-factory.bin
```

上电后默认 Wi-Fi：
- SSID：`ESP32-CC-Flasher`
- 密码：`12345678`
- 管理地址：`http://192.168.4.1`

网页内可配置连接家庭 Wi-Fi。烧录器应用仍保留 ArduinoOTA，后续更新可选择 OTA，但首次迁移不使用它。

## Halo 固件上游

基于 [DIYRuZ FreePad](https://github.com/diyruz/freepad) 的 CC2530 方案移植 P1.2–P1.7 六键、低功耗与 Zigbee2MQTT 事件。需要匹配 TI Z-Stack 与 IAR 8051 工具链。

## 数据保护

在擦除 ESP32 Flash 前，建议用 esptool 读取完整 4 MB 并校验 SHA-256。CC2530 原厂固件备份应读取两次、校验 SHA-256，并保存在本地，不要提交到公开 GitHub 仓库。不要在未确认锁定状态时对 CC2530 执行 Unlock/Erase。
