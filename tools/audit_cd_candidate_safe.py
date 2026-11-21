#!/usr/bin/env python3
"""Conservative CD candidate scanner. No UBROF record or relocation claims."""
import argparse
import hashlib
import json
import unittest
from pathlib import Path

def scan(data):
    hits = []
    for pos in range(max(0, len(data) - 13)):
        if data[pos] != 0xcd:
            continue
        length = int.from_bytes(data[pos+1:pos+5], "big")
        if not 10 <= length <= 4096 or pos+5+length > len(data):
            continue
        n = data[pos+9]
        if not n or length != n+9:
            continue
        name = data[pos+10:pos+10+n]
        if not name or not all(32 <= c <= 126 for c in name):
            continue
        tail = data[pos+10+n:pos+14+n]
        if len(tail) == 4:
            hits.append((pos, pos+5+length, name, tail))
    return hits

def audit(data):
    hits = scan(data)
    overlaps = sum(a[0] < b[1] and b[0] < a[1]
                   for i, a in enumerate(hits) for b in hits[i+1:])
    return {
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "candidate_count": len(hits),
        "candidate_offset_sha256": hashlib.sha256(
            ",".join(str(x[0]) for x in hits).encode()).hexdigest(),
        "duplicate_name_count": len(hits)-len(set(x[2] for x in hits)),
        "overlapping_candidates": overlaps,
        "record_boundaries_verified": False,
        "relocation_indices_verified": False,
        "executable_conversion": False,
    }

class Tests(unittest.TestCase):
    @staticmethod
    def record(name=b"probe", tail=b"\xff"*4):
        return (b"\xcd" + (len(name)+9).to_bytes(4,"big")
                + b"\x00"*4 + bytes([len(name)]) + name + tail)

    def test_one_record(self):
        r = audit(self.record())
        self.assertEqual(r["candidate_count"], 1)
        self.assertFalse(r["record_boundaries_verified"])

    def test_repeated_names_not_dropped(self):
        r = audit(self.record()+self.record(tail=b"\x00"*4))
        self.assertEqual(r["candidate_count"], 2)
        self.assertEqual(r["duplicate_name_count"], 1)

    def test_length_mismatch(self):
        bad = bytearray(self.record())
        bad[4] += 1
        self.assertEqual(scan(bad), [])

    def test_truncation(self):
        self.assertEqual(scan(self.record()[:-1]), [])

    def test_reject_non_ascii_name(self):
        self.assertEqual(scan(self.record(b"\x00bad")), [])

    def test_no_raw_names_or_tail_in_report(self):
        result = json.dumps(audit(self.record(b"private_symbol")))
        self.assertNotIn("private_symbol", result)
        self.assertNotIn("ffffffff", result)

    def test_not_confuse_embedded_cd(self):
        self.assertEqual(audit(b"\xcd"*100)["candidate_count"], 0)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.file is None:
        p.error("file required unless --self-test")
    print(json.dumps(audit(args.file.read_bytes()), indent=2))
