# Halo M-Key CC2530 固件

当前分支已加入 DIYRuZ FreePad 源码适配脚本，目标为六键 Zigbee2MQTT 遥控器。

- S1-S6：P1.2-P1.7，按下接地，低电平有效
- 单击、双击、长按分别产生 FreePad action；长按释放另发 release
- 六个 Zigbee endpoints
- 不使用 LED
- PM3 低功耗与 P1 下降沿中断唤醒

运行方式：
```powershell
git clone --recurse-submodules https://github.com/diyruz/freepad.git
py firmware\halo\prepare_halo_freepad.py <freepad-checkout>
py tools\check_halo_port.py <freepad-checkout>
```

**注意：静态适配脚本和 GitHub 源码检查成功，不代表已经产生 HEX。** 真实构建需要 TI Z-Stack 3.0.2 与有合法许可的 IAR 8051 编译器。当前仓库的 self-hosted IAR workflow 只有在配置 Windows runner 和环境变量后才能生成并发布 HEX。不要将通用 FreePad 或 LeTV HEX 刷入 Halo M-Key。
