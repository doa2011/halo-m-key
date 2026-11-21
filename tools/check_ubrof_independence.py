"""Check independence of heuristic slices, without exposing library bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import unittest

def audit(samples):
    groups = {}
    aligned = []
    for name, data, start, stop in samples:
        if not 0 <= start < stop < len(data):
            raise ValueError("invalid prefix bounds")
        aligned.append(data[stop:stop+4096])
        digest = hashlib.sha256(data[start:stop]).hexdigest()
        suffix = hashlib.sha256(data[stop:stop+4096]).hexdigest()
        groups.setdefault(digest, []).append({
            "sample_index": len(aligned)-1, "name": name, "prefix_length": stop-start,
            "following_4k_sha256": suffix, "next_tag": hex(data[stop]),
            "slice_length": len(data)})
    # 对齐解析终点，比较其后有限字节；重复前缀并不等于独立模块。
    comparisons = []
    for members in groups.values():
        for i, left in enumerate(members):
            for right in members[i+1:]:
                a, b = aligned[left["sample_index"]], aligned[right["sample_index"]]
                limit = min(len(a), len(b))
                common = next((j for j in range(limit) if a[j] != b[j]), limit)
                comparisons.append({"left": left["name"], "right": right["name"],
                                    "compared_bytes": limit, "common_following_bytes": common,
                                    "comparison_limit": 4096,
                                    "fully_compared": len(a) == len(b) and len(a) < 4096,
                                    "first_difference_verified": common < limit})
    return {"aligned_following_comparisons": comparisons,
            "sample_count":sum(map(len,groups.values())),
            "unique_prefix_count":len(groups),"groups":groups,
            "module_boundaries_verified":False,
            "executable_conversion":False}

class TestAudit(unittest.TestCase):
    def test_duplicate(self):
        r=audit([("a",b"xxABCz",2,5),("b",b"ABCz",0,3)])
        self.assertEqual(r["unique_prefix_count"],1)
        self.assertFalse(r["module_boundaries_verified"])
    def test_aligned_following_and_first_difference(self):
        r=audit([("a",b"xxABCsame1",2,5),("b",b"ABCsame2",0,3)])
        self.assertEqual(r["unique_prefix_count"],1)
        self.assertEqual(r["aligned_following_comparisons"][0]["common_following_bytes"],4)
        self.assertEqual(r["aligned_following_comparisons"][0]["compared_bytes"],5)
        self.assertFalse(r["module_boundaries_verified"])
    def test_short_suffix_not_overclaimed(self):
        r=audit([("a",b"ABCx",0,3),("b",b"ABCxyz",0,3)])
        self.assertEqual(r["aligned_following_comparisons"][0]["common_following_bytes"],1)
        self.assertEqual(r["aligned_following_comparisons"][0]["compared_bytes"],1)
    def test_repeated_names_are_independent_samples(self):
        r=audit([("same",b"ABCx",0,3),("same",b"ABCy",0,3)])
        c=r["aligned_following_comparisons"][0]
        self.assertEqual(c["common_following_bytes"],0)
        self.assertTrue(c["first_difference_verified"])
        self.assertEqual(r["sample_count"],2)
    def test_equal_prefix_of_suffix_is_not_full_equality(self):
        r=audit([("a",b"ABCx",0,3),("b",b"ABCxy",0,3)])
        c=r["aligned_following_comparisons"][0]
        self.assertEqual(c["common_following_bytes"],1)
        self.assertFalse(c["fully_compared"])
        self.assertFalse(c["first_difference_verified"])
    def test_distinct(self):
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
