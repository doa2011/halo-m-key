"""只导出固定结构的非敏感统计，不复制研究报告中的自由文本或数组。"""
import argparse
import json
import tempfile
import unittest
from pathlib import Path

SOURCES = ("boundaries.json", "router-boundaries.json", "standalone-ecc.json")
FIELDS = ("candidate_count", "unique_prefix_count", "archive_size")
MAX_COUNT = 100000000

def make_summary(directory):
    directory = Path(directory)
    result = {"schema_version": 1, "record_semantics_verified": False,
              "executable_conversion": False, "sources": {}}
    for filename in SOURCES:
        data = json.loads((directory / filename).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("报告不是对象")
        counts = {}
        for field in FIELDS:
            if field in data:
                value = data[field]
                if type(value) is not int or not 0 <= value <= MAX_COUNT:
                    raise ValueError("无效统计字段: " + field)
                counts[field] = value
        if "candidate_count" not in counts:
            raise ValueError("缺少候选数量: " + filename)
        result["sources"][filename] = counts
    return result

def export(directory, output):
    summary = make_summary(directory)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    return summary

class Tests(unittest.TestCase):
    def fixture(self, directory, extra=None):
        for filename in SOURCES:
            obj = {"candidate_count": 2, "archive_size": 1024,
                   "description": "c2Vuc2l0aXZl", "raw_bytes": [1,2,3],
                   "candidates": [{"payload": "deadbeef"}]}
            if extra:
                obj.update(extra)
            (Path(directory) / filename).write_text(json.dumps(obj))
    def test_no_encoded_or_raw_payload(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d)
            out = Path(d) / "public" / "summary.json"
            export(d, out)
            text = out.read_text()
            for forbidden in ("c2Vuc2l0aXZl", "deadbeef", "raw_bytes", "description", "candidates", "payload"):
                self.assertNotIn(forbidden, text)
            self.assertEqual(json.loads(text)["sources"]["boundaries.json"]["candidate_count"], 2)
    def test_reject_string_count(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d, {"candidate_count": "2"})
            with self.assertRaises(ValueError):
                make_summary(d)
    def test_reject_boolean_count(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d, {"candidate_count": True})
            with self.assertRaises(ValueError):
                make_summary(d)
    def test_reject_float_and_oversized_counts(self):
        for invalid in (2.0, MAX_COUNT + 1):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as d:
                self.fixture(d, {"candidate_count": invalid})
                with self.assertRaises(ValueError):
                    make_summary(d)

    def test_reject_missing_required_source(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d)
            (Path(d) / SOURCES[-1]).unlink()
            with self.assertRaises(FileNotFoundError):
                make_summary(d)

    def test_reject_missing_candidate_count(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d)
            p = Path(d) / SOURCES[0]
            obj = json.loads(p.read_text())
            del obj["candidate_count"]
            p.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):
                make_summary(d)

    def test_fixed_schema_and_source_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d)
            for i, filename in enumerate(SOURCES):
                p = Path(d) / filename
                obj = json.loads(p.read_text())
                obj["candidate_count"] = i + 1
                obj["unique_prefix_count"] = i
                p.write_text(json.dumps(obj))
            result = make_summary(d)
            self.assertEqual(set(result), {"schema_version", "record_semantics_verified",
                                           "executable_conversion", "sources"})
            self.assertEqual(set(result["sources"]), set(SOURCES))
            self.assertEqual([result["sources"][f]["candidate_count"] for f in SOURCES],
                             [1, 2, 3])
            self.assertFalse(result["record_semantics_verified"])
            self.assertFalse(result["executable_conversion"])

    def test_reject_negative_count(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d, {"candidate_count": -1})
            with self.assertRaises(ValueError):
                make_summary(d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--directory", default="reports")
    parser.add_argument("--output", default="public-reports/summary.json")
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=["export"], exit=False)
    else:
        export(args.directory, args.output)
        print("公开摘要已生成，仅含固定统计字段")
