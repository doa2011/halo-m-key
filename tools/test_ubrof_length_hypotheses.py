#!/usr/bin/env python3
"""C1 长度假设反证：仅合成字节，不包含第三方 SDK 数据。

精确覆盖到候选区间末尾不等于已证明 UBROF 格式。
"""
import unittest
from scan_ubrof_boundaries import examine_following, c1_local_evidence


class LengthHypothesisTests(unittest.TestCase):
    def test_exact_end_can_be_manufactured(self):
        # 这是人为构造的两个记录，证明 exact_end 仅为候选条件。
        data = bytes.fromhex("c100020102c2000103")
        rows = examine_following(data, 0, len(data))
        matching = [r for r in rows if r["exact_end"]]
        self.assertTrue(matching)
        self.assertTrue(all("record_semantics_verified" not in r for r in matching))

    def test_single_byte_mutation_breaks_two_byte_hypothesis(self):
        good = bytes.fromhex("c100020102c2000103")
        bad = bytearray(good)
        bad[2] = 0x7f
        def candidate(data):
            return next(r for r in examine_following(data, 0, len(data))
                        if r["width"] == 2 and r["endian"] == "big"
                        and not r["includes_header"])
        self.assertTrue(candidate(good)["exact_end"])
        self.assertFalse(candidate(bytes(bad))["exact_end"])

    def test_truncated_header_does_not_claim_valid_length(self):
        for data in (b"\xc1", b"\xc1\x00", b"\xc1\x00\x02"):
            with self.subTest(size=len(data)):
                rows = c1_local_evidence(data, 0, len(data))
                self.assertFalse(any(r["valid"] for r in rows if r["width"] == 4))
                candidates = examine_following(data, 0, len(data))
                # c1 00 可被一字节零长度假设“精确覆盖”，但不是已验证记录。
                # exact_end 是数值匹配，不应被当作结构真实性判据。
                if len(data) == 2:
                    self.assertTrue(any(r["exact_end"] and r["records"] == 1 for r in candidates))
                else:
                    self.assertFalse(any(r["exact_end"] for r in candidates))

    def test_c1_byte_in_payload_is_not_proof_of_new_record(self):
        data = bytes.fromhex("c1000301c102")
        rows = examine_following(data, 0, len(data))
        two_byte = next(r for r in rows if r["width"] == 2 and r["endian"] == "big"
                        and not r["includes_header"])
        self.assertEqual(two_byte["records"], 1)
        self.assertTrue(two_byte["exact_end"])
        # 负载中的 C1 不能被该候选解释自动升级为第二条记录。
        self.assertEqual(two_byte["tag_histogram"], {"0xc1": 1})


    def test_repeated_c1_zero_payload_is_not_boundary_proof(self):
        # 两段人工 C1 + 2字节零长度；重复标签与精确覆盖均可人为制造。
        data = bytes.fromhex("c10000c10000")
        rows = examine_following(data, 0, len(data))
        match = next(r for r in rows if r["width"] == 2 and r["endian"] == "big"
                     and not r["includes_header"])
        self.assertEqual(match["records"], 2)
        self.assertEqual(match["covered_bytes"], len(data))
        self.assertTrue(match["exact_end"])
        self.assertEqual(match["tag_histogram"], {"0xc1": 2})
        self.assertNotIn("record_semantics_verified", match)

    def test_boundary_shift_breaks_manufactured_exact_end(self):
        # 仅改变候选上界，不改变数据；精确覆盖并不是成员边界证据。
        data = bytes.fromhex("c10000c10000")
        full = examine_following(data, 0, len(data))
        shifted = examine_following(data, 0, len(data) - 1)
        def select(rows):
            return next(r for r in rows if r["width"] == 2
                        and r["endian"] == "big" and not r["includes_header"])
        self.assertTrue(select(full)["exact_end"])
        self.assertFalse(select(shifted)["exact_end"])
        self.assertEqual(select(shifted)["records"], 1)

    def test_zero_length_endian_ambiguity(self):
        # 两种字节序在零长度字段上完全等价；精确覆盖无法区分字节序。
        data = bytes.fromhex("c10000c10000")
        rows = examine_following(data, 0, len(data))
        selected = [r for r in rows if r["width"] == 2
                    and not r["includes_header"] and r["exact_end"]]
        self.assertEqual({r["endian"] for r in selected}, {"big", "little"})
        self.assertTrue(all(r["records"] == 2 for r in selected))
        self.assertTrue(all(r["tag_histogram"] == {"0xc1": 2} for r in selected))
        self.assertTrue(all("record_semantics_verified" not in r for r in selected))

    def test_nonzero_length_separates_endian_hypotheses(self):
        # 单个非零长度字段即可打破上述退化等价，但仍不能证明真实格式。
        data = bytes.fromhex("c1000101")
        rows = examine_following(data, 0, len(data))
        def candidate(endian):
            return next(r for r in rows if r["width"] == 2
                        and r["endian"] == endian and not r["includes_header"])
        self.assertTrue(candidate("big")["exact_end"])
        self.assertFalse(candidate("little")["exact_end"])
        self.assertNotIn("record_semantics_verified", candidate("big"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
