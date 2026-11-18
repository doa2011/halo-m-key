# ESP32_MOS_X4 临时 CC2530 烧录器

## 首次烧录方式

本版本使用 USB-UART + Espressif esptool 完整烧录，不依赖原 ESPHome OTA。GitHub Actions 会输出包含 Bootloader、Partition Table、boot_app0 和应用程序的 `cc2530-flasher-esp32dev-factory.bin`。

## GPIO

| ESP32 GPIO | CC2530 信号 |
|---|---|
| GPIO18 | DC / P2.2 |
| GPIO19 | DD / P2.1 |
| GPIO21 | RESET_N |
| GND | GND |

GPIO16/D16 与 GPIO17/D17 严格保留。18/19/21 仍须核对 MOS_X4 实物排针与板载电路后再接线。

## 构建配置

- 上游：[z9m/ESP32-CC-Tool-Pro](https://github.com/z9m/ESP32-CC-Tool-Pro)
- 固定提交：`3a5b9fc123cf660a61edad1d79502ea7b36c05fb`
- 目标：经典 ESP32 `esp32dev`
- Flash：4 MB / DIO / 40 MHz
- 分区表：`partitions.csv`
- 构建适配：`tools/prepare_esp32_flasher.py`
- 自动编译：`.github/workflows/esp32-flasher-build.yml`

## 刷机步骤

1. 先读取并保存完整 4 MB 原 Flash。
2. 断开 GPIO1/GPIO3 上的 UART 外设，尤其是 TDS 模块 TX 到 ESP32 GPIO3/RX0 的连线。
3. 安装 `py -m pip install esptool==4.9.0`。
4. 解压 Actions artifact，执行 `flash_esptool.bat COM5`（按实际串口修改）。
5. 脚本先擦除整片 Flash，再从 0x0 写入 factory 镜像。

**注意：** 该操作会清除原 ESPHome 程序、分区表、NVS、Wi-Fi 凭据和其他 Flash 数据。恢复原净水器功能时，需要通过 USB-UART 写回原始 4 MB 备份。

## 默认网络

- AP：`ESP32-CC-Flasher`
- 密码：`12345678`
- 地址：`http://192.168.4.1`

上游页面资源嵌入应用程序，不需要单独上传 LittleFS 数据镜像。LittleFS 分区用于保存 CC2530 dump 和待写入固件。
