# 2026-11-22 C1 长度反证 CI 失败与修复记录

- 分支：`feature/sdcc-build`；失败基线：`2c2a245374ece08c44dbedcffc001b6be8d09d62`。
- 失败运行：https://github.com/doa2011/halo-m-key/actions/runs/45079678996 ，Job `records` / `137384778057`。
- 真实日志：原有前缀 9 项、C1 变形 4 项通过；新增长度反证 4 项中，`test_truncated_header_does_not_claim_valid_length` 的 `size=2` 子测试失败，`AssertionError: True is not false`。
- 根因：合成字节 `c1 00` 可以被 `examine_following` 的一字节、非含头长度假设解释为零负载的候选，`exact_end=True`。原测试错误地假设所有截断头都不可能精确覆盖。
- 修复：保留扫描器所有竞争性假设；改为对两字节样本显式验证这个假阳性，对其余样本仍检查不精确覆盖。**精确覆盖不证明 UBROF 记录语义**，不据此接受零长度记录。
- 修复提交：https://github.com/doa2011/halo-m-key/commit/50055cd635ae72901146dc8de7fec5af60a471b2
- 验证状态：修复后的 GitHub Actions 待实际 Job 日志确认；未证明 C1 记录边界、真实代码段、符号、重定位或 SDCC ABI/bank 布局。
- 安全约束：不上传专有库原始字节，不发布测试 HEX，不合并 main。
- 下一步：先确认独立快速 CI 实际通过，再使用具有合法来源和独立已知结构的样本反证长度字段；避免把启发式候选当作可转换 REL。
