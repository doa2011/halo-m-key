#!/usr/bin/env python3
"""Conservative reader for the observed IAR 8051 R51 metadata prefix.

This is not a complete UBROF parser or an R51-to-REL converter. It parses
only the initial C9 attribute chain observed in two IAR 10.20.1 CC2530 objects.
Unknown records are deliberately left unparsed.
"""
import argparse
import hashlib
import json
import unittest
from pathlib import Path

PREFIX = bytes.fromhex("01 0b 05 10 14 0b 7e")
OPAQUE_HEADER_SIZE = 11
C9 = 0xC9


def take(data, pos, size, label):
    if pos < 0 or size < 0 or pos + size > len(data):
        raise ValueError(f"truncated {label} at 0x{pos:x}")
    return data[pos:pos + size]


def u32be(data, pos, label):
    return int.from_bytes(take(data, pos, 4, label), "big"), pos + 4


def parse_c9_chain(data, pos):
    records = []
    while pos < len(data) and data[pos] == C9:
        start = pos
        size, payload = u32be(data, pos + 1, "C9 record length")
        end = payload + size
        if end > len(data):
            raise ValueError(f"C9 record at 0x{start:x} exceeds file bounds")
        key_size, cursor = u32be(data, payload, "C9 key length")
        if key_size > size - 8:
            raise ValueError(f"C9 key length exceeds record at 0x{start:x}")
        key = take(data, cursor, key_size, "C9 key")
        value_size, cursor = u32be(data, cursor + key_size, "C9 value length")
        if cursor + value_size != end:
            raise ValueError(f"C9 value length mismatch at 0x{start:x}")
        value = take(data, cursor, value_size, "C9 value")
        try:
            key, value = key.decode("ascii"), value.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError(f"non-ASCII C9 attribute at 0x{start:x}") from exc
        records.append({"offset": start, "end": end, "key": key, "value": value})
        pos = end
    return records, pos, (data[pos] if pos < len(data) else None)


def parse_r51_prefix(data):
    if not data.startswith(PREFIX):
        raise ValueError("unrecognized R51 prefix; no heuristic resynchronization")
    name_size = take(data, len(PREFIX), 1, "module-name length")[0]
    if not 1 <= name_size <= 127:
        raise ValueError(f"invalid module-name length: {name_size}")
    cursor = len(PREFIX) + 1
    try:
        module = take(data, cursor, name_size, "module name").decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("module name is not ASCII") from exc
    cursor += name_size

    opaque = take(data, cursor, OPAQUE_HEADER_SIZE, "opaque module header")
    cursor += OPAQUE_HEADER_SIZE
    version_size = take(data, cursor, 1, "compiler-version length")[0]
    cursor += 1
    if not 1 <= version_size <= 32:
        raise ValueError(f"invalid compiler-version length: {version_size}")
    try:
        version = take(data, cursor, version_size, "compiler version").decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("compiler version is not ASCII") from exc
    cursor += version_size
    if cursor >= len(data) or data[cursor] != C9:
        raise ValueError("expected C9 attribute chain after observed header")

    records, stop, next_tag = parse_c9_chain(data, cursor)
    keys = [r["key"] for r in records]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate C9 attribute keys")
    return {
        "module_name": module,
        "compiler_version": version,
        "first_attribute_offset": cursor,
        "attributes": records,
        "attribute_chain_end": stop,
        "next_tag": None if next_tag is None else hex(next_tag),
        "unparsed_tail_bytes": len(data) - stop,
        "file_size": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "opaque_header_sha256": hashlib.sha256(opaque).hexdigest(),
        "complete_ubrof_parse": False,
        "executable_conversion": False,
    }


def attr(key, value):
    payload = len(key).to_bytes(4, "big") + key + len(value).to_bytes(4, "big") + value
    return b"\xc9" + len(payload).to_bytes(4, "big") + payload


def sample(name=b"hal_key"):
    return (PREFIX + bytes([len(name)]) + name
            + bytes.fromhex("bd 0b 00 03 00 53 00 83 54 20 00")
            + b"\x05" + b"10.20"
            + attr(b"__calling_convention", b"xdata_reentrant")
            + attr(b"__code_model", b"banked")
            + b"\x52opaque-tail")


class Tests(unittest.TestCase):
    def test_name_length_controls_first_attribute_offset(self):
        self.assertEqual(parse_r51_prefix(sample(b"hal_key"))["first_attribute_offset"], 0x20)
        self.assertEqual(parse_r51_prefix(sample(b"OSAL_FreePadApp"))["first_attribute_offset"], 0x28)

    def test_attribute_chain_and_unknown_tail(self):
        result = parse_r51_prefix(sample())
        self.assertEqual([x["key"] for x in result["attributes"]],
                         ["__calling_convention", "__code_model"])
        self.assertEqual(result["next_tag"], "0x52")
        self.assertFalse(result["complete_ubrof_parse"])

    def test_rejects_wrong_prefix(self):
        with self.assertRaisesRegex(ValueError, "unrecognized R51 prefix"):
            parse_r51_prefix(b"noise" + sample())

    def test_rejects_truncated_c9(self):
        data = sample()
        with self.assertRaisesRegex(ValueError, "exceeds file bounds"):
            parse_r51_prefix(data[:0x20 + 1 + 4 + 43 - 2])

    def test_rejects_inconsistent_inner_length(self):
        data = bytearray(sample())
        pos = 0x20 + 1 + 4 + 4 + len(b"__calling_convention")
        data[pos:pos + 4] = (999).to_bytes(4, "big")
        with self.assertRaisesRegex(ValueError, "value length mismatch"):
            parse_r51_prefix(bytes(data))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if args.input is None:
        ap.error("input is required unless --self-test is used")
    report = parse_r51_prefix(args.input.read_bytes())
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    print(f"{report['module_name']}: {len(report['attributes'])} C9 attributes; "
          f"stopped at 0x{report['attribute_chain_end']:x}, "
          f"next={report['next_tag']} (remaining bytes not decoded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
