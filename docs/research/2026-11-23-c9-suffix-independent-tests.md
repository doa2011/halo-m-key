# 2026-11-23 C9 后缀锚点独立反证与 CI 修复

- 实验分支：`feature/sdcc-build`，未合并 main。
- 初始提交 `66bf7d6c02a246869442933c59824acf5da362be`：新增 `tools/test_ubrof_suffix_anchors.py`，抽取独立 C9 签名扫描，覆盖偏移、截断、重复前缀、嵌套值伪锚点。
- 接入提交 `b65b2d192d497717a5f71b152369e8fff4132884`：快速 CI 执行五项合成测试，并复用同一函数扫描独立 ecc.r51 的后缀；不重新编译 SDCC。
- 失败证据：https://github.com/doa2011/halo-m-key/actions/runs/45225621656 ，Job `137871187897`，前置测试 `test_signature_in_value_is_not_boundary_proof` 失败。错误断言要求外层含嵌套属性的 C9 必然被保守解析器接受；实际外层未被接受，不能将其视为解析器故障或 UBROF 格式证据。
- 修复提交 `7ccd5000d757b1fa059bcfc508041cd55a2a280f`：删除错误的外层必然命中断言，保留嵌入值候选及不能推断模块边界的反证。
- 修复验证：https://github.com/doa2011/halo-m-key/actions/runs/45225713771 ，快速 CI 成功；GPIO：https://github.com/doa2011/halo-m-key/actions/runs/45225713943 成功。
- 安全：工作流仅上传固定公开摘要 `public-reports/summary.json`，不上传专有原始字节。
- 限制：C9 候选即使可独立解析，也不等于真实 UBROF 记录边界；0xC1 长度、符号、代码、重定位、ABI/bank 与真实 REL 转换均未验证。不得将绿色 CI 或测试 HEX 当成可用固件。
- 下一步：在合法已知结构样本上交叉验证嵌套值签名的假阳性，并继续对 0xC1 长度竞争假设做独立反证。
