#!/usr/bin/env python3
"""合成样本的 UBROF C1 边界反证测试；不读取或输出第三方库字节。

仅验证当前保守 C9 前缀解析器在尾部扰动下不会误判完整记录。
不证明 C1 语义、代码段、符号、重定位或可执行转换。
"""
import unittest
from audit_iar_ubrof_prefix import sample, parse_r51_prefix, attr


class C1MetamorphicTests(unittest.TestCase):
    def test_c1_in_unknown_tail_does_not_advance_boundary(self):
        baseline = parse_r51_prefix(sample())
        for tail in (b"\xc1", b"\xc1\xc1", b"\x00\xc1\x00",
                     b"\xc1" + attr(b"fake", b"record")):
            with self.subTest(tail_length=len(tail)):
                result = parse_r51_prefix(sample() + tail)
                self.assertEqual(result["attribute_chain_end"],
                                 baseline["attribute_chain_end"])
                self.assertEqual(result["next_tag"], baseline["next_tag"])
                self.assertFalse(result["complete_ubrof_parse"])
                self.assertFalse(result["executable_conversion"])

    def test_c1_after_valid_attribute_chain_remains_unparsed(self):
        base = sample()
        chain = base[:parse_r51_prefix(base)["attribute_chain_end"]]
        for suffix in (b"\xc1", b"\xc1\x00\xc1", b"\xc1\xff" * 10):
            with self.subTest(size=len(suffix)):
                result = parse_r51_prefix(chain + suffix)
                self.assertEqual(result["attribute_chain_end"], len(chain))
                self.assertEqual(result["next_tag"], "0xc1")
                self.assertEqual(result["unparsed_tail_bytes"], len(suffix))
                self.assertFalse(result["complete_ubrof_parse"])

    def test_c1_inside_counted_c9_length_is_not_record_marker(self):
        base = sample()
        p = parse_r51_prefix(base)["first_attribute_offset"]
        # 合法的合成属性值中不能放非 ASCII C1，但长度字段可以含 C1。
        # 故意伪造超长 C9 长度，必须报越界而非跳到下一个 C1。
        data = bytearray(base)
        data[p + 1:p + 5] = b"\x00\x00\xc1\x00"
        with self.assertRaisesRegex(ValueError, "exceeds file bounds"):
            parse_r51_prefix(bytes(data))

    def test_prefix_shift_and_fake_c1_do_not_resynchronize(self):
        for noise in (b"\xc1", b"\x00\xc1\x00", b"junk"):
            with self.subTest(noise_length=len(noise)):
                with self.assertRaisesRegex(ValueError, "no heuristic resynchronization"):
                    parse_r51_prefix(noise + sample())


if __name__ == "__main__":
    unittest.main(verbosity=2)
