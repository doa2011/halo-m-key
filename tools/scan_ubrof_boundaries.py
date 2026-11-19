"""Find candidate attribute-record chains across the complete archive.
Candidates are not verified member boundaries; emit only counts and offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unittest
from decode_ubrof_prefix import decode

def short_record_evidence(data, start, limit):
    # Aggregate only hashes and offsets; seek invariant short prefixes and
    # independently parseable known record chains after C1.
    end=min(start+256,limit)
    window=data[start:end]
    anchors=[]
    for offset in range(1,len(window)):
        if window[offset]!=0xc9:
            continue
        try:
            d=decode(window[offset:])
        except (ValueError,UnicodeError):
            continue
        if d["start"]==0 and d["counts"].get("0xc9",0)>=1:
            anchors.append(offset)
    return {"window_length":len(window),
            "prefix_hashes":{str(n):hashlib.sha256(window[:n]).hexdigest()
                             for n in (2,4,6,8,16,32,64,128,256) if n<=len(window)},
            "validated_attribute_anchors":anchors}

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

def compare_candidate_groups(hits):
    groups={}
    for h in hits:
        groups.setdefault(h["sha256"],[]).append(h)
    rows=[]
    for digest, members in groups.items():
        # Compare entire candidate-to-candidate spans, not just fixed windows.
        spans=[m["following_span"] for m in members if "following_span" in m]
        rows.append({"prefix_sha256":digest,"count":len(members),
                     "following_lengths":sorted({s["length"] for s in spans}),
                     "unique_following_hashes":len({s["sha256"] for s in spans}),
                     "unique_tail_hashes":len({s["tail_sha256"] for s in spans if "tail_sha256" in s})})
    return rows

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
            h["short_record_evidence"] = short_record_evidence(data,h["end"],limit)
            span=data[h["end"]:limit]
            h["following_span"]={"length":len(span),"sha256":hashlib.sha256(span).hexdigest(),"tail_sha256":hashlib.sha256(span[-256:]).hexdigest()}
    return {"archive_size":len(data),"archive_sha256":hashlib.sha256(data).hexdigest(),
            "candidate_count":len(hits),"unique_prefix_count":len({h["sha256"] for h in hits}),
            "candidates":hits,"candidate_groups":compare_candidate_groups(hits),"member_boundaries_verified":False,"executable_conversion":False}

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
    def test_short_record(self):
        data=b"\xc1"+b"x"*7+attr(b"a",b"b")
        r=short_record_evidence(data,0,len(data))
        self.assertIn(8,r["validated_attribute_anchors"])
        self.assertEqual(r["prefix_hashes"]["8"],hashlib.sha256(data[:8]).hexdigest())
    def test_candidate_groups(self):
        a=attr(b"a",b"b")+attr(b"c",b"d")
        r=scan(a+b"\xc1"+a+b"\xc1")
        self.assertEqual(r["candidate_groups"][0]["count"],2)
        self.assertEqual(r["candidate_groups"][0]["unique_following_hashes"],1)
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
