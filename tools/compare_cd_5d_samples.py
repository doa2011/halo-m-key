#!/usr/bin/env python3
"""Compare CD and 36-opcode-5D candidate statistics across local IAR R51 samples.

Never publish raw R51 bytes, names, source paths, or proprietary object files.
Identical aggregate signatures are not proof of identical symbol indices.
"""
import argparse
import hashlib
import json
import unittest
from pathlib import Path
from audit_cd_5d_crosscheck import audit

def compare(named_samples):
    if len(named_samples) < 2:
        raise ValueError("at least two samples required")
    if len({name for name, _ in named_samples}) != len(named_samples):
        raise ValueError("duplicate sample labels")
    rows = []
    for label, data in named_samples:
        if not data:
            raise ValueError("empty sample")
        report = audit(data)
        rows.append({
            "label": label,
            "sha256": report["sha256"],
            "size": len(data),
            "cd_candidates": report["cd_candidates"],
            "cd_duplicate_names": report["cd_duplicate_names"],
            "patterns": report["pattern_36_opcode_5d"],
            "pattern_hits_inside_cd_candidates": report["pattern_hits_inside_cd_candidates"],
        })
    pairs = []
    for i, a in enumerate(rows):
        for b in rows[i+1:]:
            pairs.append({
                "left": a["label"], "right": b["label"],
                "identical_file_hash": a["sha256"] == b["sha256"],
                "equal_candidate_counts": a["cd_candidates"] == b["cd_candidates"],
                "equal_pattern_counts": a["patterns"] == b["patterns"],
                "equal_counts_prove_index_mapping": False,
            })
    return {
        "samples": rows,
        "pairs": pairs,
        "record_boundaries_verified": False,
        "symbol_index_mapping_verified": False,
        "relocation_verified": False,
        "sdcc_rel_generated": False,
    }

class Tests(unittest.TestCase):
    def test_two_different_samples(self):
        r = compare([("T05", b"ABC"), ("T06", b"ABD")])
        self.assertEqual(len(r["pairs"]), 1)
        self.assertFalse(r["pairs"][0]["identical_file_hash"])
        self.assertTrue(r["pairs"][0]["equal_pattern_counts"])
        self.assertFalse(r["pairs"][0]["equal_counts_prove_index_mapping"])

    def test_identical_samples_are_not_mapping_proof(self):
        r = compare([("T06", b"\x36\x12\x5d"), ("T11", b"\x36\x12\x5d")])
        self.assertTrue(r["pairs"][0]["identical_file_hash"])
        self.assertFalse(r["symbol_index_mapping_verified"])

    def test_duplicate_labels_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate sample labels"):
            compare([("T05", b"A"), ("T05", b"B")])

    def test_empty_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty sample"):
            compare([("T05", b"A"), ("T06", b"")])

    def test_single_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            compare([("T05", b"A")])

    def test_report_excludes_proprietary_bytes(self):
        report = json.dumps(compare([("T05", b"PRIVATE_ZSTACK_BYTES"),
                                     ("T06", b"OTHER_PRIVATE_BYTES")]))
        self.assertNotIn("PRIVATE_ZSTACK_BYTES", report)
        self.assertNotIn("OTHER_PRIVATE_BYTES", report)

    def test_pattern_count_difference(self):
        r = compare([("T05", b"\x36\x02\x5d"), ("T06", b"\x36\x12\x5d")])
        self.assertFalse(r["pairs"][0]["equal_pattern_counts"])

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("samples", nargs="*", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if len(args.samples) < 2:
        p.error("provide at least two R51 files, or use --self-test")
    result = compare([(f"T{i:02d}", path.read_bytes())
                      for i, path in enumerate(args.samples)])
    print(json.dumps(result, indent=2))
