#!/usr/bin/env python3
"""独立验证 C9 后缀锚点：合成数据，不证明 UBROF 记录边界。"""
import unittest
from decode_ubrof_prefix import decode

SIGNATURE = b"\xc9\x00\x00\x00"

def strict_suffix_anchors(data, start=0):
    """返回所有可独立解析的 C9 候选；不跳过重叠候选。"""
    if not 0 <= start <= len(data):
        raise ValueError("start out of bounds")
    rows = []
    p = start - 1
    while True:
        p = data.find(SIGNATURE, p + 1)
        if p < 0:
            break
        try:
            r = decode(data[p:])
        except (ValueError, UnicodeError):
            continue
        if r["start"] == 0 and r["counts"].get("0xc9", 0):
            rows.append({"offset": p, "end": p + r["stop"], "counts": r["counts"]})
    return rows

def attr(k, v):
    body = len(k).to_bytes(4, "big") + k + len(v).to_bytes(4, "big") + v
    return b"\xc9" + len(body).to_bytes(4, "big") + body

class SuffixAnchorTests(unittest.TestCase):
    def test_offset_and_exclusive_start(self):
        data = b"noise" + attr(b"a", b"b")
        self.assertEqual([x["offset"] for x in strict_suffix_anchors(data)], [5])
        self.assertEqual(strict_suffix_anchors(data, 6), [])

    def test_truncated_and_false_signature(self):
        self.assertEqual(strict_suffix_anchors(b"\xc9\x00\x00\x00\xff"), [])
        self.assertEqual(strict_suffix_anchors(b"\xc9\x00\x00\x00"), [])

    def test_two_independent_candidates(self):
        data = attr(b"a", b"b") + b"noise" + attr(b"c", b"d")
        rows = strict_suffix_anchors(data)
        self.assertEqual([x["offset"] for x in rows], [0, len(attr(b"a", b"b")) + 5])

    def test_signature_in_value_is_not_boundary_proof(self):
        inner = attr(b"x", b"y")
        data = attr(b"outer", inner) + b"\xc1"
        rows = strict_suffix_anchors(data)
        # 外层含嵌套属性时保守解析器可能拒绝外层；不应要求外层必然命中。
        # 嵌入值里的签名仍可能形成可解析候选，不能据此推断模块边界。
        self.assertTrue(any(x["offset"] > 0 for x in rows))
        self.assertFalse(any("member_boundary_verified" in x for x in rows))

    def test_repeated_prefix_not_member_boundary(self):
        a = attr(b"a", b"b")
        rows = strict_suffix_anchors(a + b"\xc1" + a)
        self.assertEqual([x["offset"] for x in rows], [0, len(a) + 1])

if __name__ == "__main__":
    unittest.main(verbosity=2)
