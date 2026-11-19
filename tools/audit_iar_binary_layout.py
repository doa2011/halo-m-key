#!/usr/bin/env python3
"""Byte-level forensic inventory for TI/IAR library members.

This is deliberately an audit tool, not a converter. It preserves the original
member bytes and records offsets so a real UBROF/library decoder can be built
without treating printable strings as object metadata.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math
from pathlib import Path
from iar2sdcc.archive import extract_module_spans, extract_strings_with_offsets
from iar2sdcc.object_parser import parse_iar_object_bytes

def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts=collections.Counter(data)
    return -sum((n/len(data))*math.log2(n/len(data)) for n in counts.values())

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("library", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=6)
    args=ap.parse_args()
    blob=args.library.read_bytes()
    args.out.mkdir(parents=True,exist_ok=True)
    spans=extract_module_spans(blob)
    if not spans:
        raise SystemExit("No module spans discovered; archive framing must be decoded first")
    rows=[]
    for index,span in enumerate(spans):
        raw=blob[span.start_offset:span.end_offset]
        parsed=parse_iar_object_bytes(raw,source_path=f"{args.library}!{span.name}",module_name_hint=span.name)
        strings=[{"offset":off,"text":value} for off,value in extract_strings_with_offsets(raw,min_len=3)]
        row={
          "module":span.name,"archive_offset":span.start_offset,"archive_end":span.end_offset,
          "size":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
          "entropy_bits_per_byte":round(entropy(raw),5),
          "byte_histogram":{f"{k:02x}":v for k,v in sorted(collections.Counter(raw).items())},
          "printable_strings":strings,
          "parser_claims":{
            "calling_convention":parsed.calling_convention,"code_model":parsed.code_model,
            "data_model":parsed.data_model,
            "sections":[{"name":s.name,"kind":s.kind,"size":s.size,"raw_bytes_len":len(s.raw_bytes)} for s in parsed.sections],
            "symbols":[{"name":s.name,"binding":s.binding,"offset":s.offset,"is_function":s.is_function} for s in parsed.symbols],
            "relocations":[{"section":r.section,"offset":r.offset,"kind":r.kind,"target_symbol":r.target_symbol,"width":r.width} for r in parsed.relocations],
            "issues":parsed.issues,
          }
        }
        rows.append(row)
        if index < args.limit:
            (args.out/f"{index:02d}-{span.name}.bin").write_bytes(raw)
            (args.out/f"{index:02d}-{span.name}.hex.txt").write_text(raw[:512].hex(" ")+"\n")
    report={
      "library":str(args.library),"library_size":len(blob),
      "library_sha256":hashlib.sha256(blob).hexdigest(),"module_count":len(spans),
      "modules":rows,
      "conclusion":{
        "raw_member_bytes_preserved":True,
        "parser_decodes_machine_code":False,
        "parser_decodes_real_relocation_table":False,
        "reason":"Current parser infers symbols from printable strings and synthesizes placeholder relocations; IarSection.raw_bytes remains empty. No executable conversion may be claimed."
      }
    }
    (args.out/"binary-layout-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("IAR library:",args.library)
    print("Modules:",len(spans),"sample binaries:",min(len(spans),args.limit))
    print("Library SHA256:",report["library_sha256"])
    print("Forensic report:",args.out/"binary-layout-report.json")
    print("NO EXECUTABLE CONVERSION: machine-code and relocation decoding are not implemented")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
