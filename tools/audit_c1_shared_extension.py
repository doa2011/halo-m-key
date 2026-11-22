#!/usr/bin/env python3
"""Independent synthetic falsification of long shared bytes after heuristic C1.
Only aggregate lengths and SHA-256 are emitted; no proprietary bytes or module names.
Matching bytes are NOT proof of UBROF record boundaries, C1 semantics or relocations.
"""
import argparse
import hashlib
import json
import unittest
import zipfile
from collections import defaultdict
from io import BytesIO


def common_length(a, b):
    count = 0
    for x, y in zip(a, b):
        if x != y:
            break
        count += 1
    return count


def audit(archive):
    # 重复 ZIP 成员名会让元数据与字节读取的对应关系不明确，必须拒绝。
    names = [item.filename for item in archive.infolist()]
    if len(names) != len(set(names)):
        raise ValueError("duplicate ZIP member names")
    # JSON 默认会静默覆盖重复键，可能隐藏重复模块或偏移篡改。
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate JSON metadata key")
            obj[key] = value
        return obj
    metadata = json.loads(archive.read("record-prefix.json"),
                          object_pairs_hook=unique_object)
    if not isinstance(metadata, dict) or not metadata:
        raise ValueError("missing module metadata")
    groups = defaultdict(list)
    for name, entry in metadata.items():
        start, stop = entry["start"], entry["stop"]
        raw = archive.read(name)
        if (type(start) is not int or type(stop) is not int
                or not (0 <= start < stop < len(raw)) or raw[stop] != 0xC1):
            raise ValueError("invalid heuristic interval")
        prefix = raw[start:stop]
        groups[(len(prefix), hashlib.sha256(prefix).hexdigest())].append(raw[start:])
    # 配对数随重复样本二次增长，不能当作独立格式证据数量。
    repeated_group_count = sum(len(modules) > 1 for modules in groups.values())
    repeated_group_sizes = sorted((len(modules) for modules in groups.values() if len(modules) > 1), reverse=True)
    comparisons = []
    for modules in groups.values():
        for i, a in enumerate(modules):
            for b in modules[i + 1:]:
                shared = common_length(a, b)
                short = a if len(a) <= len(b) else b
                comparisons.append({
                    "shared_bytes": shared,
                    "shorter_remaining_bytes": len(short) - shared,
                    "shorter_tail_sha256": hashlib.sha256(short[shared:]).hexdigest(),
                    "identical_full_slices": a == b,
                })
    return {
        "module_count": len(metadata),
        "same_prefix_pair_count": len(comparisons),
        "repeated_prefix_group_count": repeated_group_count,
        "repeated_prefix_group_sizes": repeated_group_sizes,
        "comparisons": sorted(comparisons, key=lambda x: (
            x["shared_bytes"], x["shorter_remaining_bytes"],
            x["shorter_tail_sha256"])),
        "c1_length_proven": False,
        "record_boundary_proven": False,
        "relocation_proven": False,
    }


class Tests(unittest.TestCase):
    @staticmethod
    def make(rows):
        buf = BytesIO()
        metadata = {}
        with zipfile.ZipFile(buf, "w") as archive:
            for name, prefix, suffix in rows:
                archive.writestr(name, b"HDR" + prefix + b"\xc1" + suffix)
                metadata[name] = {"start": 3, "stop": 3 + len(prefix)}
            archive.writestr("record-prefix.json", json.dumps(metadata))
        buf.seek(0)
        return buf

    def test_shared_extension_with_eleven_byte_distinct_tail(self):
        common = b"A" * 14529
        rows = [("a", b"PRE", common + b"1" * 11),
                ("b", b"PRE", common + b"2" * 11)]
        with zipfile.ZipFile(self.make(rows)) as archive:
            report = audit(archive)
        item = report["comparisons"][0]
        self.assertEqual(report["same_prefix_pair_count"], 1)
        self.assertEqual(item["shared_bytes"], 3 + 1 + 14529)
        self.assertEqual(item["shorter_remaining_bytes"], 11)
        self.assertFalse(item["identical_full_slices"])

    def test_absolute_offset_is_not_used(self):
        # 两个样本的绝对起点不同，但相对切片应得到相同公共长度。
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("a", b"X" + b"ABC" + b"\xc1" + b"same" + b"x")
            archive.writestr("b", b"LONGHDR" + b"ABC" + b"\xc1" + b"same" + b"y")
            archive.writestr("record-prefix.json", json.dumps({
                "a": {"start": 1, "stop": 4},
                "b": {"start": 7, "stop": 10},
            }))
        buf.seek(0)
        with zipfile.ZipFile(buf) as archive:
            report = audit(archive)
        self.assertEqual(report["comparisons"][0]["shared_bytes"], 8)
        self.assertEqual(report["comparisons"][0]["shorter_remaining_bytes"], 1)

    def test_longer_module_continues_after_shorter_tail_diverges(self):
        # 较短模块尾部 11 字节不同，较长模块仍有后续数据。
        common = b"Q" * 128
        with zipfile.ZipFile(self.make([
            ("short", b"PRE", common + b"a" * 11),
            ("long", b"PRE", common + b"b" * 11 + b"MORE_DATA"),
        ])) as archive:
            report = audit(archive)
        pair = report["comparisons"][0]
        self.assertEqual(pair["shared_bytes"], 3 + 1 + len(common))
        self.assertEqual(pair["shorter_remaining_bytes"], 11)
        self.assertFalse(pair["identical_full_slices"])
        self.assertFalse(report["c1_length_proven"])
        self.assertFalse(report["record_boundary_proven"])
        self.assertFalse(report["relocation_proven"])

    def test_no_pairs_for_distinct_prefixes(self):
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"same"), ("b", b"ABD", b"same")])) as archive:
            self.assertEqual(audit(archive)["same_prefix_pair_count"], 0)

    def test_identical_slices_are_not_evidence_of_records(self):
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"same"), ("b", b"ABC", b"same")])) as archive:
            report = audit(archive)
        self.assertTrue(report["comparisons"][0]["identical_full_slices"])
        self.assertFalse(report["record_boundary_proven"])

    def test_invalid_interval_rejected(self):
        with zipfile.ZipFile(self.make([("a", b"ABC", b"same")])) as archive:
            raw = archive.read("a")
        for start in (-1, True, 6, None):
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as archive:
                archive.writestr("a", raw)
                archive.writestr("record-prefix.json", json.dumps({
                    "a": {"start": start, "stop": 6}}))
            buf.seek(0)
            with zipfile.ZipFile(buf) as archive:
                with self.subTest(start=start), self.assertRaises(ValueError):
                    audit(archive)

    def test_c1_stop_offset_must_point_to_real_byte(self):
        # 偏移差一字节时，即使附近存在 C1，也不能视为合法候选位置。
        raw = b"HDRABC" + bytes([0xC1]) + b"tail"
        for stop in (5, 7, 8):
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as archive:
                archive.writestr("a", raw)
                archive.writestr("record-prefix.json", json.dumps({
                    "a": {"start": 3, "stop": stop}}))
            buf.seek(0)
            with zipfile.ZipFile(buf) as archive:
                with self.subTest(stop=stop), self.assertRaisesRegex(
                        ValueError, "invalid heuristic interval"):
                    audit(archive)

    def test_multiple_c1_bytes_do_not_prove_unique_record_boundary(self):
        # 同一真实字节序列存在两个 C1；两种候选偏移均合法但无法推导语义。
        raw = b"HDRABC" + bytes([0xC1]) + b"QQ" + bytes([0xC1]) + b"tail"
        for stop in (6, 9):
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as archive:
                archive.writestr("a", raw)
                archive.writestr("record-prefix.json", json.dumps({
                    "a": {"start": 3, "stop": stop}}))
            buf.seek(0)
            with zipfile.ZipFile(buf) as archive:
                report = audit(archive)
            self.assertEqual(report["module_count"], 1)
            self.assertFalse(report["record_boundary_proven"])
            self.assertFalse(report["c1_length_proven"])

    def test_c1_payload_marker_is_not_record_evidence(self):
        # 人工负例：普通载荷恰好包含 C1；候选偏移检查通过，
        # 但不得把字节碰撞推断为真实 UBROF 记录或可转换代码。
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"payload" + bytes([0xC1]) + b"tail1"),
            ("b", b"ABC", b"payload" + bytes([0xC1]) + b"tail2"),
        ])) as archive:
            report = audit(archive)
        self.assertEqual(report["same_prefix_pair_count"], 1)
        self.assertFalse(report["record_boundary_proven"])
        self.assertFalse(report["c1_length_proven"])
        self.assertFalse(report["relocation_proven"])

    def test_unrelated_modules_with_same_c1_prefix_are_not_independent_proof(self):
        # 仅共享前缀不等于两个独立记录；后续数据完全不同。
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"first-data"),
            ("b", b"ABC", b"second-data"),
        ])) as archive:
            report = audit(archive)
        self.assertEqual(report["same_prefix_pair_count"], 1)
        self.assertEqual(report["comparisons"][0]["shared_bytes"], 4)
        self.assertFalse(report["record_boundary_proven"])

    def test_three_repeated_prefixes_are_one_group_not_three_independent_proofs(self):
        # 三个重复前缀产生三组两两比较，但仅属于一个前缀组。
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"tail1"),
            ("b", b"ABC", b"tail2"),
            ("c", b"ABC", b"tail3"),
        ])) as archive:
            report = audit(archive)
        self.assertEqual(report["same_prefix_pair_count"], 3)
        self.assertEqual(report["repeated_prefix_group_count"], 1)
        self.assertEqual(report["repeated_prefix_group_sizes"], [3])
        self.assertFalse(report["record_boundary_proven"])
        self.assertFalse(report["c1_length_proven"])

    def test_distinct_prefixes_have_zero_repeated_groups(self):
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"tail"), ("b", b"ABD", b"tail"),
        ])) as archive:
            report = audit(archive)
        self.assertEqual(report["repeated_prefix_group_count"], 0)
        self.assertEqual(report["repeated_prefix_group_sizes"], [])

    def test_two_independent_repeated_groups_have_distinct_sizes(self):
        # 分组规模而非配对数用于揭示重复样本相关性，避免虚增独立证据。
        rows = [(f"a{i}", b"ABC", b"tail" + bytes([i])) for i in range(3)]
        rows += [(f"b{i}", b"XYZ", b"tail" + bytes([i])) for i in range(2)]
        with zipfile.ZipFile(self.make(rows)) as archive:
            report = audit(archive)
        self.assertEqual(report["module_count"], 5)
        self.assertEqual(report["same_prefix_pair_count"], 4)
        self.assertEqual(report["repeated_prefix_group_count"], 2)
        self.assertEqual(report["repeated_prefix_group_sizes"], [3, 2])
        self.assertFalse(report["record_boundary_proven"])

    def test_duplicate_zip_member_names_rejected(self):
        # 不依赖 Python zipfile 对同名条目的选择规则。
        import warnings
        buf = BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(buf, "w") as archive:
                archive.writestr("a", b"HDRABC\xc1tail")
                archive.writestr("a", b"HDRABC\xc1other")
                archive.writestr("record-prefix.json", json.dumps({
                    "a": {"start": 3, "stop": 6}}))
        buf.seek(0)
        with zipfile.ZipFile(buf) as archive:
            with self.assertRaisesRegex(ValueError, "duplicate ZIP"):
                audit(archive)

    def test_duplicate_json_metadata_keys_rejected(self):
        # ZIP 文件名唯一仍不足以保证 JSON 内的模块标识唯一。
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("a", b"HDRABC\xc1tail")
            archive.writestr("record-prefix.json",
                             '{"a":{"start":3,"stop":6},"a":{"start":1,"stop":4}}')
        buf.seek(0)
        with zipfile.ZipFile(buf) as archive:
            with self.assertRaisesRegex(ValueError, "duplicate JSON metadata key"):
                audit(archive)

    def test_duplicate_nested_interval_field_rejected(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("a", b"HDRABC\xc1tail")
            archive.writestr("record-prefix.json",
                             '{"a":{"start":3,"start":1,"stop":6}}')
        buf.seek(0)
        with zipfile.ZipFile(buf) as archive:
            with self.assertRaisesRegex(ValueError, "duplicate JSON metadata key"):
                audit(archive)

    def test_valid_metadata_with_real_c1_byte_accepted(self):
        # 正例：确保合法元数据确实走到真实 0xC1 边界检查，
        # 避免反证测试只验证提前拒绝而未覆盖正常路径。
        with zipfile.ZipFile(self.make([
            ("a", b"ABC", b"tail1"), ("b", b"ABC", b"tail2")
        ])) as archive:
            report = audit(archive)
        self.assertEqual(report["module_count"], 2)
        self.assertEqual(report["same_prefix_pair_count"], 1)
        self.assertEqual(report["comparisons"][0]["shared_bytes"], 3 + 1 + 4)
        self.assertFalse(report["record_boundary_proven"])

    def test_report_does_not_expose_names_or_raw_bytes(self):
        with zipfile.ZipFile(self.make([
            ("SECRET_NAME", b"PRIVATE", b"SECRET_PAYLOAD"),
            ("OTHER_NAME", b"PRIVATE", b"SECRET_PAYLOAd")])) as archive:
            report = json.dumps(audit(archive))
        for secret in ("SECRET_NAME", "OTHER_NAME", "PRIVATE", "SECRET_PAYLOAD"):
            self.assertNotIn(secret, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if not args.artifact:
        parser.error("artifact ZIP required")
    with zipfile.ZipFile(args.artifact) as archive:
        print(json.dumps(audit(archive), indent=2))
