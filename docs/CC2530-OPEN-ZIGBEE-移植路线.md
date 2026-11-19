# Halo M-Key：开源 CC2530 Zigbee 协议栈移植路线

## 结论

主路线 B 改为评估并移植 `faronov/cc2530-zigbee`，A 路线（TI Z-Stack 3.0.2 + SDCC-IAR）保留为备用研究分支。

上游固定基线：
- Firmware: `faronov/cc2530-zigbee@655438fb1c54fe9f97cc30950c66ecdaddc20846`
- LLVM MCS51: `faronov/llvm-project@2c3d9541c965dee8d3e35bdc81ea494e4ab02dc2`
- License: 上游 README 声明 BSD-3-Clause，集成时仍须保留 LICENSE 与版权声明。

## 已有证据和限制

上游项目是运行在 CC2530 上的独立 Zigbee EndDevice 实现，不依赖 TI 预编译 Z-Stack 库。当前主线构建使用专用 LLVM MCS51，不再支持其历史 SDCC 固件构建流程。

上游 README/验证文档记录：
- LG ESL29 Rev0.3 板上曾完成普通 Zigbee 入网和 ZHA interview 的硬件观察。
- 当前实现仍是实验性子集，不是 Zigbee 生产级/完整一致性实现。
- 其设备应用包含演示用合成温湿度值，不可直接当作 Halo 按键应用。
- Sleepy EndDevice、可靠休眠/唤醒、完整重连及所有互操作能力仍有未关闭事项。
- 上游 FULL/硬件验收状态必须按每个具体提交核实，不能把历史证据自动视为当前提交的验收。

## Halo 硬件约束（用户实测）

六个按键按下接地，低电平有效：
- S1 = P1.2 / QFN40 pin 8
- S2 = P1.3 / QFN40 pin 7
- S3 = P1.4 / QFN40 pin 6
- S4 = P1.5 / QFN40 pin 5
- S5 = P1.6 / QFN40 pin 38
- S6 = P1.7 / QFN40 pin 37

没有连接 LED。不得初始化或驱动 LED GPIO。

上游 LG ESL29 Rev0.3 板级定义占用了 P1.2（显示 BUSY）、P1.3-P1.5（板级 strap）、P1.6/P1.7（UART/未来 I2C）。因此不能把 LG 板级文件直接改名后用于 Halo；必须新建独立 `halo_m_key` board profile，确保只初始化 Halo 实测引脚及射频必需引脚。

## 开发阶段与验收门槛

1. **上游基线复现**：固定两仓库 commit，LLVM 编译器构建成功，生成上游 LG join 参考 HEX/ELF/receipt。该产物明确标记 NOT HALO。
2. **板级移植**：新增 Halo board profile；核查 P1.2-P1.7 与调试、时钟、射频复用冲突；保留复位默认状态安全。
3. **应用层移植**：移除合成传感器应用，建立六个按键事件；单击、双击、长按和长按释放使用明确的 ZCL/厂商事件映射。
4. **网络互操作**：先验证入网、Basic/Power/Identify 等基础 cluster，再验证 Zigbee2MQTT interview 和 action 暴露。ZHA 成功不等于 Z2M 成功。
5. **Sleepy EndDevice**：实现 poll/父节点关系/唤醒窗口/重试/持久化与重新入网；不能仅调用 PM3 就宣称 SED 完成。
6. **实机功耗**：分别测量上电、入网、空闲休眠、按键唤醒/发送、重入网电流，记录电源和测量仪器。

## 发布规则

- 上游 LG join HEX 仅为参考构建，不得烧录到 Halo。
- 只有 Halo board profile 真实链接、HEX/ELF/receipt 完整、内存与启动检查通过后，才可标记为 Halo 实验固件。
- 只有实际 CC2530 硬件入网、Zigbee2MQTT interview、六键事件和睡眠唤醒验证通过后，才可标记为可用版本。
- A 路线生成的符号桩/占位转换对象绝不可链接进正式固件。
