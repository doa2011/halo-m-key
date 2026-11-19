"""Find candidate attribute-record chains across the complete archive.
Candidates are not verified member boundaries; emit only counts and offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unittest
from decode_ubrof_prefix import decode

def scan(data):
    hits=[]
    p=0
    while True:
        p=data.find(b"\xc9\x00\x00\x00",p)
        if p<0:
            break
        try:
            r=decode(data[p:])
        except (ValueError, UnicodeError):
            p+=1
            continue
        count=r["counts"].get("0xc9",0)
        if count>=2 and r["stop"]>0:
            end=p+r["stop"]
            hits.append({"start":p,"end":end,"counts":r["counts"],
                         "next_tag":r["next_tag"],
                         "sha256":hashlib.sha256(data[p:end]).hexdigest()})
            p=end
        else:
            p+=1
    return {"archive_size":len(data),"archive_sha256":hashlib.sha256(data).hexdigest(),
            "candidate_count":len(hits),"unique_prefix_count":len({h["sha256"] for h in hits}),
            "candidates":hits,"member_boundaries_verified":False,"executable_conversion":False}

def attr(k,v):
    b=len(k).to_bytes(4,"big")+k+len(v).to_bytes(4,"big")+v
    return b"\xc9"+len(b).to_bytes(4,"big")+b

class Tests(unittest.TestCase):
    def test_offsets(self):
        a=attr(b"a",b"b")+attr(b"c",b"d")
        r=scan(b"xxx"+a+b"\xc1"+a+b"\xc1")
        self.assertEqual(r["candidate_count"],2)
        self.assertEqual(r["unique_prefix_count"],1)
        self.assertEqual(r["candidates"][0]["start"],3)
        self.assertFalse(r["member_boundaries_verified"])
    def test_noise(self):
        self.assertEqual(scan(b"abc")["candidate_count"],0)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("archive",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if not unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful():
        raise SystemExit(1)
    r=scan(a.archive.read_bytes())
    a.out.write_text(json.dumps(r,indent=2))
    print("Whole archive candidates:",r["candidate_count"],"unique prefixes:",r["unique_prefix_count"])
    assert r["candidate_count"]>0
