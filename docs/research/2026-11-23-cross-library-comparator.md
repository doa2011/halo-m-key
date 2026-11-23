# 2026-11-23：跨库候选区间比较器独立化（非固件）

## 基线与证据
- 基线 HEAD `28568c10f5a87d207425823cb82383d9e385d4c6`；UBROF 快速 Run [45104623568](https://github.com/doa2011/halo-m-key/actions/runs/45104623568) 的 records Job 成功，输出 `[(45336, False, False), (65536, False, True)]`，Artifact 14787355388。
- 第一组 45336 字节仅表示候选区间结束；第二组 65536 字节命中比较上限；均不证明 UBROF 模块边界。
- 2026-11-23 新增 `tools/compare_ubrof_candidate_spans.py` 和 `tools/test_compare_ubrof_candidate_spans.py`；从工作流内嵌脚本提取同一比较逻辑，增加左/右区间单独结束、零长区间、偏移对齐、上限掩盖真实差异、真实首差异、输入非法等合成回归。
- 工作流 `ubrof-fast.yml` 已调用独立测试；独立测试不下载 SDK、不调用 SDCC，完整工作流后续研究步骤仍使用已固定的公开研究输入。
- 这轮的 GitHub 提交依次为 `bc8b46a`、`5ef5366`、`ccafcce`。实际 CI 结果必须以对应 HEAD 的 Job 日志为准，不能以提交成功代替测试成功。

## 边界和安全
- 比较器的 `candidate_boundaries_verified`、`record_semantics_verified`、`executable_conversion` 固定为 false。
- 仅公开合成测试、偏移、长度、哈希和统计，不提交专有原始库字节；仍需审计全部报告字段。
- 待验证：真实 UBROF C1 长度与语义、代码段、符号、重定位、ABI/bank、真实单模块 REL；禁止把占位 HEX 视为固件。
