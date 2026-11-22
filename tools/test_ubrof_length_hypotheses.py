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
                self.assertFalse(any(r["exact_end"] for r in examine_following(data, 0, len(data))))

    def test_c1_byte_in_payload_is_not_proof_of_new_record(self):
        data = bytes.fromhex("c1000301c102")
        rows = examine_following(data, 0, len(data))
        two_byte = next(r for r in rows if r["width"] == 2 and r["endian"] == "big"
                        and not r["includes_header"])
        self.assertEqual(two_byte["records"], 1)
        self.assertTrue(two_byte["exact_end"])
        # 负载中的 C1 不能被该候选解释自动升级为第二条记录。
        self.assertEqual(two_byte["tag_histogram"], {"0xc1": 1})


if __name__ == "__main__":
    unittest.main(verbosity=2)
