"""Strict partial UBROF record decoder; unknown records stop decoding."""
import argparse
import collections
import json
from pathlib import Path

WIDTH = {0xc9: 4, 0xcd: 4, 0xc6: 2, 0xd3: 2}

def decode(data):
    start = data.find(b"\xc9\x00\x00\x00")
    if start < 0:
        raise ValueError("attribute anchor missing")
    p = start
    records = []
    while p < len(data):
        tag = data[p]
        width = WIDTH.get(tag)
        if width is None or p+1+width > len(data):
            break
        size = int.from_bytes(data[p+1:p+1+width], "big")
        end = p+1+width+size
        if end > len(data):
            raise ValueError(f"truncated record at {p}")
        payload = data[p+1+width:end]
        row = {"offset":p,"tag":hex(tag),"size":size,"end":end}
        if tag == 0xc9:
            n = int.from_bytes(payload[:4],"big")
            if n+8 > size:
                raise ValueError("invalid attribute key length")
            m = int.from_bytes(payload[4+n:8+n],"big")
            if n+8+m != size:
                raise ValueError("invalid attribute value length")
            row.update(key=payload[4:4+n].decode("ascii"),value=payload[8+n:].decode("ascii"))
        records.append(row)
        p=end
    return {"start":start,"stop":p,"next_tag":hex(data[p]) if p<len(data) else None,
            "counts":dict(collections.Counter(r["tag"] for r in records)),
            "records":records,"executable_conversion":False}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("directory",type=Path)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    result={}
    for f in sorted(args.directory.glob("*.bin")):
        r=decode(f.read_bytes())
        assert r["counts"].get("0xc9",0)>0
        result[f.name]=r
        print(f.name,r["counts"],"stop",r["stop"],r["next_tag"])
    if not result:
        raise SystemExit("no samples")
    args.out.write_text(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
