# Halo M-Key (CC2530) 低功耗固件移植

> **当前状态：Halo M-Key 六键映射已实测；FreePad 源码适配与静态检查已通过。Halo 专用 HEX 仍需在安装 TI Z-Stack 3.0.2 和 IAR 8051 的 Windows 构建机上完成真实编译，尚未发布可刷写固件。**

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

## Halo M-Key 固件目标

基于 [DIYRuZ FreePad](https://github.com/diyruz/freepad) 移植，目标功能：
- 六键独立 action：单击、双击、长按；长按释放另有 release 事件
- Zigbee2MQTT FreePad 兼容
- 无 LED 硬件配置
- P1.2-P1.7 下降沿中断唤醒，FreePad PM3 低功耗配置

移植脚本：`firmware/halo/prepare_halo_freepad.py`
移植验证：`tools/check_halo_port.py`
说明：`docs/HALO-M-KEY-FreePad移植.md`

## 构建状态

- GitHub Actions `Halo M-Key FreePad Source Validation` 已验证源码补丁、六键映射和 IAR 项目 XML。
- 该 CI **不生成 HEX**。
- 真正编译依赖 TI Z-Stack 3.0.2 和有合法许可的 IAR Embedded Workbench for 8051。
- `.github/workflows/halo-m-key-iar-build.yml` 提供 self-hosted Windows runner 构建入口；runner 标签为 `iar8051`、`zstack302`，并需设置 `ZSTACK_HOME`、`IARBUILD_EXE`。

## ESP32_MOS_X4 临时烧录器

ESP32_MOS_X4 已有经典 ESP32 esptool factory 镜像构建配置。GPIO16/D16、GPIO17/D17 保留；CC2530 烧录接口临时分配 GPIO18=DC、GPIO19=DD、GPIO21=RESET。首次刷机前务必备份完整 4 MB Flash。详见 `docs/ESP32-MOS-X4接线与OTA.md`。

## 许可证与数据保护

FreePad 上游采用 GPL-3.0；TI Z-Stack SDK 与 IAR 工具链遵循各自许可，不随本仓库打包。不要把 Halo 原厂固件备份提交到公开仓库。
