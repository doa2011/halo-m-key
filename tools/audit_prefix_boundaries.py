#!/usr/bin/env python3
"""Falsification checks for repeated byte prefixes and heuristic boundaries.

This is NOT a UBROF parser. Only aggregate counts and SHA256 are printed.
"""
import argparse
import hashlib
import json
import unittest
from pathlib import Path

def inspect(data, prefix):
    if not prefix:
        raise ValueError("empty prefix")
    offsets = [i for i in range(len(data) - len(prefix) + 1)
               if data.startswith(prefix, i)]
    overlapping = sum(b < a + len(prefix) for a, b in zip(offsets, offsets[1:]))
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "prefix_hex": prefix.hex(),
        "occurrences": len(offsets),
        "overlapping_pairs": overlapping,
        "unique_prefix_boundary_proven": False,
        "record_length_proven": False,
        "record_semantics_proven": False,
    }

class Tests(unittest.TestCase):
    def test_repeated_prefix_not_unique_boundary(self):
        r = inspect(b"ABCDxxABCD", b"ABCD")
        self.assertEqual(r["occurrences"], 2)
        self.assertFalse(r["unique_prefix_boundary_proven"])

    def test_overlapping_repeats(self):
        r = inspect(b"AAAAA", b"AAA")
        self.assertEqual(r["occurrences"], 3)
        self.assertEqual(r["overlapping_pairs"], 2)

    def test_truncated_prefix(self):
        self.assertEqual(inspect(b"AB", b"ABC")["occurrences"], 0)

    def test_empty_prefix_rejected(self):
        with self.assertRaises(ValueError):
            inspect(b"abc", b"")

    def test_binary_c1_is_not_a_record_boundary(self):
        r = inspect(bytes([0xc1, 0x00, 0xc1, 0xff]), bytes([0xc1]))
        self.assertEqual(r["occurrences"], 2)
        self.assertFalse(r["record_length_proven"])
        self.assertFalse(r["record_semantics_proven"])

    def test_no_raw_bytes_leak(self):
        report = json.dumps(inspect(b"SECRET_SOURCE_BYTE_SEQUENCE", b"SEQ"))
        self.assertNotIn("SECRET_SOURCE", report)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?", type=Path)
    p.add_argument("--prefix", default="c1", help="hexadecimal byte prefix")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.file is None:
        p.error("file required unless --self-test")
    try:
        prefix = bytes.fromhex(args.prefix)
        report = inspect(args.file.read_bytes(), prefix)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps(report, indent=2))
