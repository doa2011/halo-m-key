#!/usr/bin/env python3
"""Audit identical heuristic prefixes across modules, without publishing raw bytes.

A matching prefix does NOT establish a UBROF record boundary or format semantics.
Input: local Actions artifact ZIP containing record-prefix.json and matching *.bin.
Output: counts, lengths, SHA256 only; never names, bytes, or SDK contents.
"""
import argparse
import hashlib
import json
import unittest
import zipfile
from collections import defaultdict

def audit(z):
    entries = json.loads(z.read("record-prefix.json"))
    groups = defaultdict(list)
    for name, info in entries.items():
        raw = z.read(name)
        start, stop = info["start"], info["stop"]
        if not (0 <= start < stop <= len(raw)):
            raise ValueError("invalid prefix interval")
        if raw[stop] != 0xc1 if stop < len(raw) else True:
            raise ValueError("claimed C1 stop is inconsistent")
        records = info["records"]
        if not records or records[0]["offset"] != start:
            raise ValueError("record list does not start at prefix")
        for idx, record in enumerate(records):
            if record["end"] <= record["offset"]:
                raise ValueError("nonpositive candidate interval")
            if idx and record["offset"] != records[idx-1]["end"]:
                raise ValueError("noncontiguous candidate intervals")
        if records[-1]["end"] != stop:
            raise ValueError("last candidate does not end at stop")
        digest = hashlib.sha256(raw[start:stop]).hexdigest()
        groups[(stop-start, digest)].append(name)
    return {
        "module_count": len(entries),
        "unique_prefixes": len(groups),
        "groups": sorted([{"length": n, "sha256": digest, "module_count": len(names)}
                          for (n,digest),names in groups.items()],
                         key=lambda x:(-x["module_count"],x["sha256"])),
        "record_boundary_proven": False,
        "c1_semantics_proven": False,
        "relocation_proven": False,
    }

class Tests(unittest.TestCase):
    @staticmethod
    def make(entries):
        from io import BytesIO
        out=BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            info={}
            for name, prefix in entries:
                data=b"HEADER"+prefix+bytes([0xC1])+b"TAIL"
                z.writestr(name,data)
                info[name]={"start":6,"stop":6+len(prefix),
                            "records":[{"offset":6,"end":6+len(prefix)}]}
            z.writestr("record-prefix.json",json.dumps(info))
        return BytesIO(out.getvalue())
    def test_duplicate_prefixes_group(self):
        with zipfile.ZipFile(self.make([("a.bin",b"ABC"),("b.bin",b"ABC")])) as z:
            r=audit(z)
        self.assertEqual(r["unique_prefixes"],1)
        self.assertEqual(r["groups"][0]["module_count"],2)
        self.assertFalse(r["record_boundary_proven"])
    def test_distinct_prefixes_not_grouped(self):
        with zipfile.ZipFile(self.make([("a.bin",b"ABC"),("b.bin",b"ABD")])) as z:
            self.assertEqual(audit(z)["unique_prefixes"],2)
    def test_wrong_stop_rejected(self):
        with zipfile.ZipFile(self.make([("a.bin",b"ABC")])) as z:
            raw=z.read("a.bin")
            meta=json.loads(z.read("record-prefix.json"))
        meta["a.bin"]["stop"]=7
        with zipfile.ZipFile(self.make([("a.bin",b"ABC")])) as z:
            from io import BytesIO
            buf=BytesIO()
            with zipfile.ZipFile(buf,"w") as dest:
                dest.writestr("a.bin",raw)
                dest.writestr("record-prefix.json",json.dumps(meta))
            buf.seek(0)
            with zipfile.ZipFile(buf) as bad:
                with self.assertRaises(ValueError):audit(bad)
    def test_report_has_no_names_or_bytes(self):
        with zipfile.ZipFile(self.make([("PRIVATE.bin",b"PRIVATE_CONTENT")])) as z:
            s=json.dumps(audit(z))
        self.assertNotIn("PRIVATE",s)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("artifact",nargs="?")
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        raise SystemExit(0 if r.wasSuccessful() else 1)
    if not a.artifact:p.error("artifact ZIP required")
    with zipfile.ZipFile(a.artifact) as z:print(json.dumps(audit(z),indent=2))
