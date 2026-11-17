# Halo M-Key (CC2530) 低功耗固件移植

> **状态：硬件映射已实测；Halo Zigbee HEX 与 ESP32-MOS-X4 烧录器 BIN 均尚未完成。** 本仓库目前是可追踪的移植工作区，不包含可直接刷写的固件。请勿刷入其他硬件的 LeTV HEX。

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

## 子项目与上游

- **ESP32 上位机**：参考 [ESP32-CC-Tool-Pro](https://github.com/z9m/ESP32-CC-Tool-Pro)。需要先确认 ESP32_MOS_X4 的空闲 GPIO、外设负载和重映射方案，之后再编译。
- **Halo 固件**：基于 [DIYRuZ FreePad](https://github.com/diyruz/freepad) 的 LeTV CC2530 方案移植 P1.2–P1.7 六键、低功耗与 Zigbee2MQTT 事件。需要匹配 TI Z-Stack 与 IAR 8051 工具链。

## CI 真实能力

`hardware-validation.yml` 在每次 push/PR 自动检查 6 键测量数据及头文件掩码，**不声称产出 HEX/BIN**。计划中的编译任务需先提交完整、可复现的项目源码及工具链配置，之后增加 firmware build 与 artifact 上传。闭源 IAR/Z-Stack 依赖不能靠空的 CI 步骤解决。

## 数据保护

优先使用 CC Debug 协议读取两次、校验 SHA-256，保存本地原厂 Flash；未知锁定状态下不要 Unlock/Erase。**不要把原厂固件备份直接提交到公开 GitHub 仓库**，可能涉及版权与设备敏感数据。

详见 [备份与烧录](docs/备份与烧录.md)、[开发任务](docs/开发任务.md)。
