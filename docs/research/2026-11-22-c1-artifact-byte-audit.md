# 2026-11-22：基线 Artifact 真实 C1 字节复核（非敏感统计）

## 来源与可复现方法

- GitHub Actions 基线：run 44518101073，commit `227777daa2d1ee5159ae27a3caae3455d673d3b3`。
- 下载原始分析 Artifact ID `14527497579`，ZIP SHA-256：`655477337ca69b0e991cfba734b0768efcac4b58afc6e2dd577a5376c0667f46`。
- 在**本地**执行 `python3 tools/audit_c1_shared_extension.py /path/to/artifact.zip`；仅保留统计结果，不提交 ZIP、原始 .bin、十六进制文本或包含专有数据的原始 JSON。
- 独立复核方法：读取 ZIP 内 `record-prefix.json` 的 8 个 `start/stop`，逐个检查 `raw[stop] == 0xC1`，分别统计 `raw[start:stop].count(b"\\xc1")`、`raw[stop+1:].count(b"\\xc1")`；对 `raw[start:stop]` 的长度及 SHA-256 分组。

## 实际结果

- 8 个候选停止偏移均命中真实字节 `0xC1`，但**8 个候选前缀内部也各含 1 个 `0xC1`**，因此停止位置并非该切片的首次 C1，不能依据单字节唯一性证明边界。
- 候选点之后 C1 数量的排序分布：`[13, 14, 14, 14, 14, 14, 126, 165]`；候选点之前：`[1, 1, 1, 1, 1, 1, 1, 1]`；包含候选点的切片总 C1 数量排序分布：`[15, 16, 16, 16, 16, 16, 128, 167]`。
- 候选前缀仅有 2 个重复组：长度 27,602 字节的组有 2 个样本，长度 24,829 字节的组有 6 个样本；不是 8 份独立格式证据。
- 原始元数据中的 8 个 `executable_conversion` 均为 `false`。这只是原分析器状态，不是已证明不能转换。
- 以上数据为真实字节的可复核**观察值**，不是 UBROF 格式规范或 C1 记录定义。

## 结论与后续实验

当前 `record_boundary_proven = false`、`c1_length_proven = false`、`relocation_proven = false` 仍必须保持。下一步应使用合法公开的 UBROF 文档或独立、合法生成的已知结构样本，验证记录起止、长度编码和跨记录一致性；随后才考虑代码段、符号偏移、重定位与 SDCC REL 映射。不能通过选择某个 C1 偏移来倒推出记录边界；也不能把 ret 占位或绿色 CI 当作真实固件。

本记录仅公开统计与校验哈希，不公开原始专有 SDK/库字节。