# ESP32_MOS_X4 烧录器适配

目标板：用户现有 ESP32_MOS_X4，现运行 ESPHome；现有 YAML 使用 `board: esp32dev`、Arduino framework，并启用带加密的 ESPHome OTA。

## 必须保留的 GPIO

- GPIO16 / D16：进水阀 MOS 驱动，**禁止使用**。
- GPIO17 / D17：废水/冲洗阀 MOS 驱动，**禁止使用**。
- GPIO18 / GPIO19：TDS UART，禁止占用。
- GPIO21 / GPIO22：I²C SDA/SCL，禁止占用。
- GPIO23：状态灯；GPIO4/13 流量计；GPIO14 蜂鸣器；GPIO25/32 输入；GPIO26/27 MOS 输出，也视为已占用。

当前没有足够证据指定 CC 调试接口的 GPIO。不要沿用上游 GPIO4/5/6，也不要沿用此前错误提出的 GPIO18/19/21。先根据 ESP32_MOS_X4 原理图、排针丝印和通断测试，确定三个未占用且电气合适的脚。

## 上游工程现状

上游：https://github.com/z9m/ESP32-CC-Tool-Pro

当前上游 `platformio.ini` 默认 `env:esp32s3` / `esp32-s3-devkitc-1`，而目标 ESPHome 配置为 `esp32dev`（经典 ESP32）。必须新增/调整 classic ESP32 构建环境，不能把 S3 固件刷到经典 ESP32。

## OTA 迁移原则

当前 ESPHome 已启用 `ota: - platform: esphome` 和加密。理论上可以通过现有 ESPHome OTA 通道一次性上传兼容的 ESP32 应用镜像，但必须满足：目标是经典 ESP32、镜像是 app-only OTA image（不能用含 bootloader/partition table 的 factory image）、匹配现有 OTA 分区表且小于 OTA slot、OTA 加密认证正确。成功切换后 ESPHome OTA/API 不再存在；后续应在烧录器固件中实现自己的 OTA 更新入口，或保留 USB 恢复方案。

ESPHome 官方文档：
- https://esphome.io/components/ota/esphome/
- https://esphome.io/guides/cli/

## 安全要求

1. 不要在未确认 GPIO 和分区大小前上传。
2. 先通过 ESPHome OTA 上传一个保留原有 API/Wi-Fi/OTA 的过渡 ESPHome 固件并验证稳定（如果需要调整分区或 OTA 权限）；不应贸然覆盖唯一可远程恢复的应用。
3. 记录 Flash 容量、分区表、OTA slot 大小、当前 app 大小及目标 app 大小。
4. 保留 USB-UART 串口恢复路径；OTA 失败或分区不兼容时，不能保证自动恢复。
