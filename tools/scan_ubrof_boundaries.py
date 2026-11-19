"""Find candidate attribute-record chains across the complete archive.
Candidates are not verified member boundaries; emit only counts and offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unittest
from decode_ubrof_prefix import decode

def c1_local_evidence(data,start,limit):
    rows=[]
    for width in (1,2,3,4):
        for endian in (("big",) if width==1 else ("big","little")):
            for inclusive in (False,True):
                size=int.from_bytes(data[start+1:start+1+width],endian)
                end=start+size if inclusive else start+1+width+size
                valid=start+1+width<=end<limit
                rows.append({"width":width,"endian":endian,"inclusive":inclusive,
                    "valid":valid,"candidate_length":end-start,
                    "next_tag":hex(data[end]) if valid else None})
    return rows

def examine_following(data, start, limit):
    # Compare hypotheses against candidate chain boundaries; do not select a format.
    results = []
    for width in (1, 2, 3, 4):
        for endian in ("big", "little"):
            for includes_header in (False, True):
                p = start
                count = 0
                tags = {}
                while p + 1 + width <= limit and count < 100000:
                    tag = data[p]
                    size = int.from_bytes(data[p+1:p+1+width], endian)
                    end = p + size if includes_header else p + 1 + width + size
                    if end < p+1+width or end > limit:
                        break
                    tags[hex(tag)] = tags.get(hex(tag), 0) + 1
                    count += 1
                    p = end
                results.append({"width":width,"endian":endian,
                    "includes_header":includes_header,"records":count,
                    "covered_bytes":p-start,"exact_end":p==limit,
                    "tag_histogram":tags})
    return results

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
    for i,h in enumerate(hits):
        if h["next_tag"] == "0xc1":
            limit = hits[i+1]["start"] if i+1<len(hits) else len(data)
            h["following_hypotheses"] = examine_following(data,h["end"],limit)
            h["c1_local_evidence"] = c1_local_evidence(data,h["end"],limit)
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
    def test_following_hypothesis(self):
        data=bytes.fromhex("c100020102c2000103")
        r=examine_following(data,0,len(data))
        match=next(x for x in r if x["width"]==2 and x["endian"]=="big" and not x["includes_header"])
        self.assertEqual(match["records"],2)
        self.assertTrue(match["exact_end"])
    def test_c1_local(self):
        rows=c1_local_evidence(bytes.fromhex("c100020102c2000103"),0,9)
        row=next(x for x in rows if x["width"]==2 and x["endian"]=="big" and not x["inclusive"])
        self.assertEqual(row["candidate_length"],5)
        self.assertEqual(row["next_tag"],"0xc2")
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
