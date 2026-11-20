# Halo M-Key Windows IAR 构建节点部署

本仓库不分发 TI Z-Stack SDK 或 IAR 编译器。真实 HEX 构建需要一台安装了工具链的 Windows x64 主机，并将它注册为本仓库的 GitHub Actions self-hosted runner。该主机可以是单独的 Windows 虚拟机，不必是日常工作电脑。

## 1. 安装工具链

### TI Z-Stack 3.0.2

从 [TI Z-STACK 官方页面](https://www.ti.com/tool/Z-STACK) 获取 CC253x Z-Stack 3.0.2。TI 页面可能要求登录或出口审批。安装后确认 SDK 根目录下存在：

- `Components\`
- `Projects\zstack\`
- `Tools\CC2530DB\`

### IAR EW8051

安装 IAR Embedded Workbench for 8051。TI 对 CC2530 Z-Stack 3.0.2 推荐 EW8051 10.20.1；TI 官方说明可向 IAR 申请 30 天评估版本，长期使用需按 IAR 许可条款购买授权。

IAR 官网：[IAR Embedded Workbench](https://www.iar.com/embedded-development-tools/iar-embedded-workbench)

安装后在 PowerShell 查找命令行构建工具：

```powershell
Get-ChildItem "C:\Program Files (x86)\IAR Systems" -Filter IarBuild.exe -Recurse -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty FullName
```

## 2. 设置构建环境变量

以管理员身份打开 PowerShell，按实际安装目录设置（以下路径仅为示例）：

```powershell
[Environment]::SetEnvironmentVariable("ZSTACK_HOME", "C:\ti\Z-Stack 3.0.2", "Machine")
[Environment]::SetEnvironmentVariable("IARBUILD_EXE", "C:\Program Files (x86)\IAR Systems\Embedded Workbench 8.4\common\bin\IarBuild.exe", "Machine")
```

重新登录 Windows，或重启 GitHub Actions Runner 服务，确保服务进程读取到新环境变量。

## 3. 注册 GitHub Runner

在仓库页面打开：

`Settings → Actions → Runners → New self-hosted runner → Windows → x64`

按 GitHub 页面给出的命令下载并配置 runner。配置时添加以下自定义标签：

`iar8051,zstack302`

启动 runner 并确认仓库 Settings 页面显示状态为 Idle / Online。

安全建议：
- 使用专用 Windows VM 或专用低权限账户。
- 不要把 runner 注册到含有敏感数据的个人电脑账户。
- 当前 IAR workflow 仅由 `workflow_dispatch` 手动触发，不对外部 PR 自动执行。
- 不要将 IAR License、TI 下载凭据或其他私密文件提交到 Git 仓库。

## 4. 触发真实 HEX 编译

进入 GitHub：

`Actions → Halo M-Key IAR CC2530 HEX Build → Run workflow`

Runner 会执行以下流程：
1. 从 DIYRuZ 获取 FreePad 源码和 zstack-lib 子模块；
2. 将 FreePad 工程放入 TI SDK 的 HomeAutomation 工程目录，以满足原工程相对路径；
3. 执行 Halo M-Key 六键板级补丁；
4. 执行静态映射检查；
5. 调用 IAR `IarBuild.exe` 编译 `HALO_M_KEY_PM3`；
6. 检查真实 HEX 和 MAP 文件存在且非空；
7. 生成 SHA256，并上传 GitHub Actions artifact。

成功产物名称：`halo-m-key-cc2530-hex`，内含：
- `halo-m-key-cc2530-pm3.hex`
- `halo-m-key-cc2530-pm3.map`
- `SHA256.txt`
- `FREEPAD-LICENSE`

如果 IAR 评估授权过期、SDK 路径错误、头文件缺失或链接失败，workflow 必须失败，不会上传伪造 HEX。

## 5. 后续自动构建

首次真实构建成功并完成人工验证后，再考虑将 IAR workflow 从手动触发改为 push/tag 触发。保留 self-hosted runner 标签和许可环境，后续代码更新即可自动编译。

## 6. 当前边界

源码适配和静态 CI 已通过，但这不等于编译通过。没有 IAR 8051 + TI Z-Stack 3.0.2 环境时，GitHub hosted runner 无法合法地产生本项目的真实 HEX。请不要刷写上游通用 FreePad 或 LeTV HEX。
