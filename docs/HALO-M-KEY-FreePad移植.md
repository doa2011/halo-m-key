# Halo M-Key V0.6：DIYRuZ FreePad 移植

## 功能目标

- CC2530，Zigbee End Device。
- Zigbee2MQTT 兼容 DIYRuZ FreePad 的设备识别和 action 上报。
- 六个物理按键：单击、双击、长按事件。
- 不使用板载 LED（当前硬件没有连接 LED）。
- 空闲进入 FreePad PM3 低功耗模式，P1 中断唤醒。
- 只接受单键输入；同时按下多个键时忽略该采样，避免误识别。

## 已测硬件映射

| 按键 | QFN40 脚 | GPIO | 按下状态 | 逻辑 endpoint |
|---|---:|---|---|---:|
| S1 | 8 | P1.2 | LOW | 1 |
| S2 | 7 | P1.3 | LOW | 2 |
| S3 | 6 | P1.4 | LOW | 3 |
| S4 | 5 | P1.5 | LOW | 4 |
| S5 | 38 | P1.6 | LOW | 5 |
| S6 | 37 | P1.7 | LOW | 6 |

按键按下接地。P1.2-P1.7 配置为 GPIO 输入、内部上拉、下降沿中断。LED 数量为 0。

## 上游与许可证

上游： https://github.com/diyruz/freepad
上游版本：FreePad 2.0.7（项目源码 master 的 2.0.x 布局）
Z-Stack reusable library： https://github.com/diyruz/zstack-lib
上游 FreePad 为 GPL-3.0；TI Z-Stack SDK / IAR 编译器另受其各自许可约束。保留上游版权及 LICENSE，不将 TI SDK 或 IAR 工具链打包进仓库。

## 当前移植实现

`firmware/halo/prepare_halo_freepad.py` 对干净的 FreePad checkout 执行确定性修改：

1. 新增 `HAL_BOARD_HALO_M_KEY` 板型。
2. 将逻辑按钮数改为 6。
3. 将 HAL 按键扫描改为 P1.2-P1.7 六个独立低有效输入。
4. 配置 P1 下降沿中断与内部上拉，保留 FreePad 的 OSAL 按键去抖、multi-function 单击/双击/长按定时逻辑。
5. 将 P1 位掩码映射到 endpoint 1-6。
6. 使用 PM3、无 Touchlink 的 IAR 配置，降低代码体积和待机功耗。

FreePad 的 multi-function 模式默认用 250 ms 窗口区分单击/双击，长按起始约为 1 秒（250+750 ms）。释放事件按上游行为额外上报。Zigbee2MQTT action 事件格式沿用 FreePad 既有 converter：`1_single`、`1_double`、`1_hold`、`1_release` 等。

## 构建要求（真实 HEX）

FreePad 是 TI Z-Stack 3.0.2 + IAR 8051 工程，不是 PlatformIO 工程。必须准备：
- Windows 10/11 x64 构建机（可作为 GitHub Actions self-hosted runner）；
- TI Z-Stack 3.0.2 SDK；
- IAR EW8051 10.20.1（TI 对 CC2530 Z-Stack 3.0.2 推荐的版本），并具有完整功能的评估授权或商业授权。不要使用 4 KB 限制的 KickStart 版本。

将 FreePad 仓库放在：
`<ZSTACK_HOME>\Projects\zstack\HomeAutomation\freepad`
并初始化 `zstack-lib` 子模块。运行：

```powershell
py firmware\halo\prepare_halo_freepad.py $env:ZSTACK_HOME\Projects\zstack\HomeAutomation\freepad
py tools\check_halo_port.py $env:ZSTACK_HOME\Projects\zstack\HomeAutomation\freepad
& "$env:IARBUILD_EXE" "$env:ZSTACK_HOME\Projects\zstack\HomeAutomation\freepad\CC2530DB\GenericApp.ewp" -build HALO_M_KEY_PM3 -log all
```

输出 HEX 应位于：
`CC2530DB\HALO_M_KEY_PM3\Exe\`
构建脚本必须检查 HEX 文件真实存在、非空，并保存 MAP 文件；不得把上游通用 FreePad HEX 或头文件伪装成 Halo 固件。

## Zigbee2MQTT

固件保留 FreePad 的 Manufacturer/Model ID 与 ZCL endpoint/cluster 设计，便于复用 Zigbee2MQTT FreePad 支持。配对时按上游 FreePad 方式长按 S1 进入入网/重置流程。由于此板没有 LED，不能使用 LED 闪烁判断入网成功，应在 Zigbee2MQTT 日志和设备列表确认。

参考：
- https://www.zigbee2mqtt.io/devices/DIYRuZ_FreePad.html
- https://github.com/diyruz/freepad
- https://github.com/diyruz/zstack-lib

## 自动编译环境配置

IAR 8051 Evaluation Edition 是限时评估版；KickStart 是 4 KB 限制版，不能用于完整 Z-Stack 工程。

本仓库不能合法分发 IAR 编译器或 TI SDK。普通 GitHub-hosted runner 不预装这两套工具，且 IAR 授权不能通过公开 workflow 绕过。请在一台 Windows 机器安装上述工具，然后在 GitHub 仓库 Settings → Actions → Runners → New self-hosted runner 添加 runner，平台选 Windows x64，标签额外添加 `iar8051`、`zstack302`。在该 runner 服务进程环境中设置：

- `ZSTACK_HOME`：TI Z-Stack 3.0.2 安装根目录；
- `IARBUILD_EXE`：IAR 的 `IarBuild.exe` 完整路径。

启动 runner 后，在 Actions → Halo M-Key IAR CC2530 HEX Build → Run workflow 手动触发首次构建。成功后会产生 HEX、MAP、SHA256 和上游 LICENSE artifact。后续可将此 workflow 改为 push/PR 自动触发。

## 当前验证边界

静态适配和脚本检查不等于 IAR 编译成功。当前还未生成 Halo 专用 HEX，也未实测 P1 中断唤醒、Zigbee 配对、action payload 或 PM3 电流。只有 IAR Build 成功、HEX/MAP 存在并完成实机测试后，才能发布正式固件。
