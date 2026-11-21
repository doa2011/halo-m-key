#!/usr/bin/env python3
"""Cross-check observed CD-name and 36-opcode-5D patterns, without inferring a relocation table.

Only aggregate statistics and hashes are emitted. Pattern hits are not UBROF records.
"""
import argparse
import hashlib
import json
import unittest
from pathlib import Path
from audit_cd_candidate_safe import scan

OPCODES = (0x02, 0x12, 0x90)

def candidates(data):
    """Return raw candidate offsets for local analysis, never serialize them."""
    return [(i, data[i + 1]) for i in range(max(0, len(data) - 2))
            if data[i] == 0x36 and data[i + 1] in OPCODES and data[i + 2] == 0x5d]

def audit(data):
    names = scan(data)
    patterns = candidates(data)
    by_opcode = {f"{op:02x}": sum(op == value for _, value in patterns)
                 for op in OPCODES}
    duplicate_names = len(names) - len(set(hit[2] for hit in names))
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "cd_candidates": len(names),
        "cd_duplicate_names": duplicate_names,
        "pattern_36_opcode_5d": by_opcode,
        "pattern_hits_inside_cd_candidates": sum(
            1 for offset, _ in patterns
            if any(start <= offset < stop for start, stop, _, _ in names)),
        "cd_record_boundaries_verified": False,
        "symbol_index_mapping_verified": False,
        "relocation_verified": False,
        "sdcc_rel_generated": False,
    }

class Tests(unittest.TestCase):
    @staticmethod
    def cd(name=b"relay"):
        return (b"\xcd" + (len(name) + 9).to_bytes(4, "big")
                + b"\x00" * 4 + bytes([len(name)]) + name + b"\xff" * 4)

    def test_three_opcode_patterns(self):
        data = b"\x36\x02\x5d\x36\x12\x5d\x36\x90\x5d"
        self.assertEqual(audit(data)["pattern_36_opcode_5d"],
                         {"02": 1, "12": 1, "90": 1})

    def test_truncated_pattern_not_counted(self):
        self.assertEqual(candidates(b"\x36\x12"), [])

    def test_nonmatching_opcode_not_counted(self):
        self.assertEqual(candidates(b"\x36\x13\x5d"), [])

    def test_duplicate_names_are_ambiguous(self):
        report = audit(self.cd() + self.cd())
        self.assertEqual(report["cd_duplicate_names"], 1)
        self.assertFalse(report["symbol_index_mapping_verified"])

    def test_opaque_cd_field_can_contain_pattern(self):
        report = audit(self.cd().replace(b"\x00" * 4, b"\x36\x12\x5d\x00", 1))
        self.assertEqual(report["pattern_36_opcode_5d"]["12"], 1)
        self.assertEqual(report["pattern_hits_inside_cd_candidates"], 1)
        self.assertFalse(report["relocation_verified"])

    def test_nonascii_name_cannot_establish_cd_boundary(self):
        # A raw 36-12-5D pattern alone does not prove a valid CD candidate.
        report = audit(self.cd(b"\\x36\\x12\\x5d"))
        self.assertEqual(report["pattern_36_opcode_5d"]["12"], 1)
        self.assertEqual(report["cd_candidates"], 0)
        self.assertEqual(report["pattern_hits_inside_cd_candidates"], 0)
        self.assertFalse(report["relocation_verified"])

    def test_no_proprietary_bytes_in_report(self):
        report = json.dumps(audit(self.cd(b"private_internal_symbol")))
        self.assertNotIn("private_internal_symbol", report)

    def test_no_claims_of_conversion(self):
        self.assertFalse(audit(b"\x36\x02\x5d")["sdcc_rel_generated"])

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
