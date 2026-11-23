"""公开 Artifact 上传前的保守审计：仅允许预定 JSON 报告，不处理原始 SDK 字节。"""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

ALLOWED = {
    "independence.json", "boundaries.json", "router-boundaries.json",
    "cross-library.json", "cross-library-following.json",
    "standalone-ecc.json", "ecc-suffix-anchors.json",
}
FORBIDDEN = {"raw", "raw_bytes", "bytes", "binary", "payload", "hexdump",
             "hex_dump", "base64", "blob", "source_bytes", "data_hex"}

def check_report(path):
    path = Path(path)
    if path.name not in ALLOWED or path.suffix != ".json":
        raise ValueError(f"未列入允许上传清单: {path.name}")
    if path.stat().st_size > 2_000_000:
        raise ValueError(f"报告过大: {path.name}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in FORBIDDEN:
                    raise ValueError(f"禁止字段: {key}")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(obj)
    return True

def audit(directory):
    directory = Path(directory)
    files = sorted(directory.iterdir())
    if not files:
        raise ValueError("报告目录为空")
    for path in files:
        if not path.is_file():
            raise ValueError(f"禁止目录项: {path.name}")
        check_report(path)
    return len(files)

class Tests(unittest.TestCase):
    def test_allow_counts_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "boundaries.json"
            p.write_text(json.dumps({"sha256": "a"*64, "candidate_count": 2}))
            self.assertEqual(audit(d), 1)
    def test_reject_binary(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "raw.bin").write_bytes(b"secret")
            with self.assertRaises(ValueError):
                audit(d)
    def test_reject_nested_raw(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "boundaries.json"
            p.write_text('{"candidates":[{"raw_bytes":[1,2,3]}]}')
            with self.assertRaises(ValueError):
                audit(d)
    def test_reject_unknown_json(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "new-report.json").write_text("{}")
            with self.assertRaises(ValueError):
                audit(d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--directory", default="reports")
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=["audit"], exit=False)
    else:
        print(f"允许上传 JSON 报告数: {audit(args.directory)}")
