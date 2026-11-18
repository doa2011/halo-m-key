# ESP32_MOS_X4：从 ESPHome 切换到 CC2530 Flasher（esptool 串口方案）

## 设备依据

根据此前提供的设备调试信息：
- 芯片：经典 ESP32，Revision 3.1
- Flash：4 MB，40 MHz，DIO
- 原 ESPHome：`esp32dev`、Arduino framework、加密 OTA
- 原分区表为自定义双 OTA 布局；本次烧录器改用独立的 4 MB 分区表，以便为 CC2530 dump/待写入固件提供足够 LittleFS 空间。

原分区布局与本次分区表不同，不能只刷 app-only 镜像后继续沿用旧分区表。本方案采用 factory merged image 并从 0x0 完整写入。

## 新分区表

| 名称 | 类型 | 偏移 | 大小 |
|---|---|---:|---:|
| nvs | data/nvs | 0x9000 | 0x5000 |
| otadata | data/ota | 0xE000 | 0x2000 |
| app0 | app/ota_0 | 0x10000 | 0x140000 |
| app1 | app/ota_1 | 0x150000 | 0x140000 |
| spiffs | data/spiffs | 0x290000 | 0x160000 |
| coredump | data/coredump | 0x3F0000 | 0x10000 |

## 烧录前必须做

1. **先备份整个 ESP32 4 MB Flash**，包括当前 ESPHome 固件、分区表、NVS 和配置数据。
2. 保存原 ESPHome YAML、secrets（离线保管）以及当前编译镜像。
3. 断开连接 ESP32 UART0 的外设，特别是接到 GPIO3/RX0 的 TDS 模块 TX 线，避免干扰 ROM 下载模式。
4. 准备 USB 数据线、可稳定供电的 USB-UART 和正确的串口驱动。
5. 确认目标确实是经典 ESP32 和 4 MB Flash；不要把本镜像用于 ESP32-S3 或其他芯片。

备份命令（Windows 示例）：

```powershell
py -m pip install esptool==4.9.0
py -m esptool --chip esp32 --port COM5 --baud 460800 read_flash 0x0 0x400000 esp32-mos-x4-original-4mb.bin
certutil -hashfile esp32-mos-x4-original-4mb.bin SHA256
```

## 烧录

解压 GitHub Actions artifact，在包含 `cc2530-flasher-esp32dev-factory.bin` 的目录运行：

```powershell
py -m esptool --chip esp32 --port COM5 --baud 460800 erase_flash
py -m esptool --chip esp32 --port COM5 --baud 460800 write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB 0x0 cc2530-flasher-esp32dev-factory.bin
```

也可以运行 `flash_esptool.bat COM5`。

该操作会完全擦除原有 Flash，清除原 ESPHome 程序、分区表、NVS、Wi-Fi 凭据及其他数据。必须先完成备份。烧录完成后 ESPHome API/OTA 和原 HA 实体不再运行。

## 启动与网络

- 默认 AP SSID：`ESP32-CC-Flasher`
- 默认 AP 密码：`12345678`
- 默认网页：`http://192.168.4.1`
- 网页可设置家庭 Wi-Fi，切换到 STA 模式后通过串口日志或路由器 DHCP 列表查 IP。

## 后续恢复

如需恢复净水器 ESPHome：
- 使用 esptool 通过 USB 串口恢复原固件和原分区表；
- 若要完整恢复原状态，使用之前备份的完整 4 MB Flash 镜像写回 0x0；
- 单独刷入 app-only 镜像不能恢复原 NVS、分区表或历史配置。

## 引脚分配

| ESP32 GPIO | 用途 | 状态 |
|---|---|---|
| 18 | CC2530 DC | 临时分配 |
| 19 | CC2530 DD | 临时分配 |
| 21 | CC2530 RESET_N | 临时分配 |
| 16 / D16 | 保留 | 不使用 |
| 17 / D17 | 保留 | 不使用 |

GPIO18/19/21 在原净水器方案中承担过 TDS UART/I²C 相关功能；当前临时固件不再运行原净水器控制逻辑。

## 参考

- [Espressif esptool v4：合并烧录镜像与串口写入](https://docs.espressif.com/projects/esptool/en/release-v4/esp32/esptool/basic-commands.html)
- [ESPHome 原生 OTA](https://esphome.io/components/ota/esphome/)
