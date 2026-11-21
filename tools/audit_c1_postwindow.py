#!/usr/bin/env python3
"""对启发式 0xC1 停止点后的窗口进行独立反证；不解析或输出专有字节。"""
import argparse
import hashlib
import json
import unittest
import zipfile
from collections import defaultdict

def audit(archive, window=128):
    if window <= 0:
        raise ValueError("window must be positive")
    metadata = json.loads(archive.read("record-prefix.json"))
    groups = defaultdict(int)
    for name, entry in metadata.items():
        raw = archive.read(name)
        stop = entry["stop"]
        if not isinstance(stop, int) or not (0 <= stop < len(raw)):
            raise ValueError("invalid stop")
        if raw[stop] != 0xC1:
            raise ValueError("stop is not C1")
        tail = raw[stop + 1:stop + 1 + window]
        if len(tail) != window:
            raise ValueError("insufficient post-C1 bytes")
        prefix = raw[entry["start"]:stop]
        key = (hashlib.sha256(prefix).hexdigest(), hashlib.sha256(tail).hexdigest())
        groups[key] += 1
    return {
        "module_count": len(metadata),
        "distinct_prefix_tail_pairs": len(groups),
        "group_sizes": sorted(groups.values(), reverse=True),
        "window_bytes": window,
        "c1_length_proven": False,
        "record_boundary_proven": False,
        "ubrof_semantics_proven": False,
    }

class Tests(unittest.TestCase):
    def make(self, rows):
        from io import BytesIO
        buffer = BytesIO()
        metadata = {}
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, prefix, tail in rows:
                archive.writestr(name, prefix + b"\\xc1" + tail)
                metadata[name] = {"start": 0, "stop": len(prefix)}
            archive.writestr("record-prefix.json", json.dumps(metadata))
        buffer.seek(0)
        return buffer

    def test_equal_prefix_equal_tail(self):
        with zipfile.ZipFile(self.make([("a", b"A", b"1234"), ("b", b"A", b"1234")])) as z:
            self.assertEqual(audit(z, 4)["group_sizes"], [2])

    def test_equal_prefix_different_tail(self):
        with zipfile.ZipFile(self.make([("a", b"A", b"1234"), ("b", b"A", b"1235")])) as z:
            self.assertEqual(audit(z, 4)["group_sizes"], [1, 1])

    def test_short_tail_rejected(self):
        with zipfile.ZipFile(self.make([("a", b"A", b"12")])) as z:
            with self.assertRaises(ValueError):
                audit(z, 4)

    def test_no_semantic_claim_or_private_bytes(self):
        with zipfile.ZipFile(self.make([("secret.bin", b"PRIVATE", b"ABCD")])) as z:
            report = audit(z, 4)
        self.assertFalse(report["record_boundary_proven"])
        self.assertFalse(report["c1_length_proven"])
        self.assertNotIn("PRIVATE", json.dumps(report))
        self.assertNotIn("secret.bin", json.dumps(report))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--window", type=int, default=128)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if not args.artifact:
        parser.error("artifact ZIP required")
    with zipfile.ZipFile(args.artifact) as archive:
        print(json.dumps(audit(archive, args.window), indent=2))
