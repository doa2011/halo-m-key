# Halo M-Key (CC2530) 低功耗固件移植

> **状态：Halo 六键硬件映射已实测；ESP32 烧录器已加入经典 ESP32 构建适配与 OTA 代码，等待 GitHub Actions 首次编译验证。Halo Zigbee HEX 尚未完成。** 本仓库目前不应被视为已实机验证的完整固件发布。

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

本次采用临时转换方案：ESP32_MOS_X4 暂停净水器 ESPHome 功能，临时运行 CC2530 Flasher。GPIO16/D16、GPIO17/D17 由用户明确要求保留，烧录器不分配、不配置这两个脚。

| ESP32 GPIO | CC2530 信号 |
|---|---|
| GPIO18 | DC / P2.2 |
| GPIO19 | DD / P2.1 |
| GPIO21 | RESET_N |
| GND | GND |

18/19/21 是临时模式下释放 TDS UART/I²C 后的候选分配；仍须核对 MOS_X4 实物引出和板载电路，再接线。详见 `docs/ESP32-MOS-X4接线与OTA.md`。

## ESP32 自动编译

`esp32-flasher-build.yml` 使用固定上游提交 `3a5b9fc123cf660a61edad1d79502ea7b36c05fb`，将上游 ESP32-S3 工程适配到经典 ESP32 `esp32dev`，并加入 ArduinoOTA。push/PR 自动编译；成功后上传 app-only BIN、SHA256、manifest 和 GPL 对应源码 artifact；推送 `v*` 标签时发布 GitHub Release。

CI 通过不等于实物 OTA 已验证。首次烧录前仍需核实实际 OTA 分区大小、芯片/Flash 型号、GPIO 引出和 USB 恢复能力。

## Halo 固件上游

基于 [DIYRuZ FreePad](https://github.com/diyruz/freepad) 的 CC2530 方案移植 P1.2–P1.7 六键、低功耗与 Zigbee2MQTT 事件。需要匹配 TI Z-Stack 与 IAR 8051 工具链。

## 数据保护

优先使用 CC Debug 协议读取两次、校验 SHA-256，保存本地原厂 Flash；未知锁定状态下不要 Unlock/Erase。不要把原厂固件备份直接提交到公开 GitHub 仓库。
