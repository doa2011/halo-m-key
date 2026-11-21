"""Check independence of heuristic slices, without exposing library bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import unittest

def audit(samples):
    groups = {}
    for name, data, start, stop in samples:
        if not 0 <= start < stop < len(data):
            raise ValueError("invalid prefix bounds")
        digest = hashlib.sha256(data[start:stop]).hexdigest()
        suffix = hashlib.sha256(data[stop:stop+4096]).hexdigest()
        groups.setdefault(digest, []).append({
            "name": name, "prefix_length": stop-start,
            "following_4k_sha256": suffix, "next_tag": hex(data[stop]),
            "slice_length": len(data)})
    # 对齐解析终点，比较其后有限字节；重复前缀并不等于独立模块。\n    aligned = {name: data[stop:stop+4096] for name, data, start, stop in samples}\n    comparisons = []\n    for members in groups.values():\n        for i, left in enumerate(members):\n            for right in members[i+1:]:\n                a, b = aligned[left["name"]], aligned[right["name"]]\n                limit = min(len(a), len(b))\n                common = next((j for j in range(limit) if a[j] != b[j]), limit)\n                comparisons.append({"left": left["name"], "right": right["name"],\n                                    "compared_bytes": limit, "common_following_bytes": common,\n                                    "comparison_limit": 4096})\n    return {"aligned_following_comparisons": comparisons,\n            "sample_count":sum(map(len,groups.values())),
            "unique_prefix_count":len(groups),"groups":groups,
            "module_boundaries_verified":False,
            "executable_conversion":False}

class TestAudit(unittest.TestCase):
    def test_duplicate(self):
        r=audit([("a",b"xxABCz",2,5),("b",b"ABCz",0,3)])
        self.assertEqual(r["unique_prefix_count"],1)
        self.assertFalse(r["module_boundaries_verified"])
    def test_aligned_following_and_first_difference(self):\n        r=audit([("a",b"xxABCsame1",2,5),("b",b"ABCsame2",0,3)])\n        self.assertEqual(r["unique_prefix_count"],1)\n        self.assertEqual(r["aligned_following_comparisons"][0]["common_following_bytes"],4)\n        self.assertEqual(r["aligned_following_comparisons"][0]["compared_bytes"],5)\n        self.assertFalse(r["module_boundaries_verified"])\n    def test_short_suffix_not_overclaimed(self):\n        r=audit([("a",b"ABCx",0,3),("b",b"ABCxyz",0,3)])\n        self.assertEqual(r["aligned_following_comparisons"][0]["common_following_bytes"],1)\n        self.assertEqual(r["aligned_following_comparisons"][0]["compared_bytes"],1)\n    def test_distinct(self):
        self.assertEqual(audit([("a",b"ABCz",0,3),("b",b"ABDz",0,3)])["unique_prefix_count"],2)
    def test_bounds(self):
        with self.assertRaises(ValueError):
            audit([("a",b"ABC",0,3)])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("directory",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    tests=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TestAudit))
    if not tests.wasSuccessful():
        raise SystemExit(1)
    rows=json.loads((a.directory/"record-prefix.json").read_text())
    report=audit([(n,(a.directory/n).read_bytes(),v["start"],v["stop"]) for n,v in rows.items()])
    a.out.write_text(json.dumps(report,indent=2))
    print("Heuristic samples:",report["sample_count"],"independent prefixes:",report["unique_prefix_count"])
    assert report["sample_count"]>0
