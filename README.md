# Halo M-Key (CC2530) 低功耗固件移植

> **状态：Halo 六键硬件映射已实测；ESP32 烧录器和 Halo Zigbee HEX 尚未完成。** 本仓库是可追踪的移植工作区，不包含可直接刷写的正式固件。请勿刷入其他硬件的 LeTV HEX。

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

## ESP32_MOS_X4 主机约束

用户现有主机为 ESP32_MOS_X4，ESPHome 配置 `board: esp32dev`、Arduino framework，已启用加密 ESPHome OTA。GPIO16/D16 和 GPIO17/D17 分别连接进水阀、废水/冲洗阀 MOS 驱动，**严禁占用**。GPIO18/19 已用于 TDS UART，GPIO21/22 用于 I²C，GPIO23 为状态灯；GPIO4/13 为流量计，GPIO14 蜂鸣器，GPIO25/32 为输入，GPIO26/27 为阀/泵输出。不能再把 18/19/21 当作烧录器候选脚。

ESP32 烧录器上游 [ESP32-CC-Tool-Pro](https://github.com/z9m/ESP32-CC-Tool-Pro) 当前 `platformio.ini` 默认目标是 ESP32-S3，不是本机的 `esp32dev`。需要移植到经典 ESP32，并核实 Flash/OTA 分区和空闲 GPIO 后再生成 OTA app image。详情见 [ESPHome OTA 迁移方案](docs/ESPHome-OTA迁移方案.md)。

## Halo 固件上游

基于 [DIYRuZ FreePad](https://github.com/diyruz/freepad) 的 LeTV CC2530 方案移植 P1.2–P1.7 六键、低功耗与 Zigbee2MQTT 事件。需要匹配 TI Z-Stack 与 IAR 8051 工具链。

## CI 真实能力

`hardware-validation.yml` 自动检查六键测量数据及头文件掩码，**不声称产出 HEX/BIN**。只有提交完整、可复现源码与匹配工具链后，才增加真正的固件构建和 Release。

## 数据保护

优先使用 CC Debug 协议读取两次、校验 SHA-256，保存本地原厂 Flash；未知锁定状态下不要 Unlock/Erase。**不要把原厂固件备份直接提交到公开 GitHub 仓库**。

详见 `docs/备份与烧录.md`、`docs/开发任务.md`。