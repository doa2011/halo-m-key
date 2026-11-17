# ESPHome OTA 切换到 CC2530 Flasher

## 当前设备配置（从用户的 `20261010.yaml` 检查）

- `esp32.board: esp32dev`
- `esp32.framework.type: arduino`
- `ota: - platform: esphome`
- OTA 使用加密，密钥引用 `!secret api_encryption_key`
- 未看到显式 `partitions:` / 自定义分区表
- 未从 YAML 确认实际 Flash 容量及 OTA app slot 大小

## 结论

**技术上可以尝试通过当前 ESPHome OTA 服务一次性替换为非 ESPHome 的 ESP32 应用固件，但目前不能保证可行。** 需要目标应用镜像适配经典 ESP32（`esp32dev` / ESP32-WROOM 类硬件）、当前分区布局、inactive OTA app slot 容量，并通过现有加密 OTA 服务认证。上传成功后设备将不再运行 ESPHome，因此原 ESPHome API/OTA 服务消失。

ESPHome CLI 支持上传预编译文件（`--file`），对于无法从镜像头推断 OTA 平台的文件，需要指定 OTA 端口；加密设备还需要正确的 OTA key。具体命令应在核对本机 ESPHome 版本与目标镜像格式后再执行。参考：https://esphome.io/guides/cli/ 与 https://esphome.io/components/ota/esphome/。

## 镜像和分区要求

1. 只使用应用分区 OTA 镜像（app-only）；不能把包含 bootloader/partition table 的 factory image 当作普通应用 OTA 镜像上传。
2. 目标镜像必须是经典 ESP32 架构，不能使用上游默认 ESP32-S3 构建结果。
3. 镜像大小必须小于当前 inactive OTA app slot；必须从当前设备构建产物/分区表读取准确值，不能猜测。
4. OTA 协议加密密钥必须与当前 ESPHome 配置一致。不要把 `secrets.yaml`、密钥或 Wi-Fi 凭据提交到 GitHub。
5. OTA 成功切换后，ESPHome 的 API、OTA 组件和设备实体都不再存在；新烧录器固件需自行实现后续 OTA（如 Web OTA / ArduinoOTA / HTTP update），否则后续更新需 USB 串口。

## 断电和回滚风险

- 普通 OTA 应用更新通常写入非活动 app slot，完成校验后再切换启动槽；但分区表/bootloader 更新是另一类风险更高的操作。本项目第一阶段不更新 bootloader 和 partition table。
- 在切换前备份 ESPHome YAML、`secrets.yaml`（离线保管，不提交仓库）、ESPHome build 目录里的分区表和 OTA app 镜像。
- 确认可用 USB-UART 串口恢复方式，记录当前 ESP32 MAC、Flash ID/容量、ESPHome 版本、芯片 revision。
- 不要在未核实 OTA slot 大小和目标镜像大小时执行切换。

## GPIO 禁用清单

依据现有 RO 净水器 YAML：

| GPIO | 当前用途 | Flasher 使用 |
|---|---|---|
| 16 / D16 | 进水阀 MOS | 禁止 |
| 17 / D17 | 废水/冲洗阀 MOS | 禁止 |
| 18 / 19 | TDS UART | 禁止 |
| 21 / 22 | I²C SDA/SCL | 禁止 |
| 23 | 状态 LED | 已占用 |
| 4 / 13 | 流量计 | 已占用 |
| 14 | 蜂鸣器 | 已占用 |
| 25 / 32 | 输入传感器 | 已占用 |
| 26 / 27 | 阀/泵 MOS | 已占用 |

当前不能从 YAML alone 指定安全的三根调试 GPIO；需结合 ESP32_MOS_X4 板级原理图、排针和实物通断确认。不要照抄上游 GPIO4/5/6；GPIO6 通常是经典 ESP32 SPI Flash 信号。

## 适配目标

上游 https://github.com/z9m/ESP32-CC-Tool-Pro 当前 `platformio.ini` 默认 `esp32-s3-devkitc-1`。需要建立 `esp32dev` / classic ESP32 构建环境，检查依赖与应用大小，并将实际确认的 CC Debug DC/DD/RESET GPIO写入 `src/main.cpp`。本仓库暂不声称有已编译或 OTA 验证通过的烧录器镜像。
