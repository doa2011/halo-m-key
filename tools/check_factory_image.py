#!/usr/bin/env python3
"""Sanity-check a merged classic ESP32 4 MB factory image."""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: check_factory_image.py <factory.bin>")

path = Path(sys.argv[1])
data = path.read_bytes()
FLASH_SIZE = 0x400000
BOOTLOADER = 0x1000
PARTITIONS = 0x8000
BOOT_APP0 = 0xE000
APP = 0x10000

if not data:
    raise SystemExit("ERROR: empty factory image")
if len(data) > FLASH_SIZE:
    raise SystemExit(f"ERROR: factory image {len(data)} exceeds 4 MB flash")
if data[BOOTLOADER] != 0xE9:
    raise SystemExit(f"ERROR: no ESP image header at bootloader offset 0x{BOOTLOADER:X}")
if data[PARTITIONS:PARTITIONS + 2] != bytes((0xAA, 0x50)):
    raise SystemExit("ERROR: partition table magic not found at 0x8000")
if data[APP] != 0xE9:
    raise SystemExit(f"ERROR: no ESP application image header at 0x{APP:X}")
if len(data) <= APP:
    raise SystemExit("ERROR: factory image ends before application image")

print(f"Factory image: {path}")
print(f"Size: {len(data)} bytes ({len(data) / FLASH_SIZE:.1%} of 4 MB flash address space)")
print(f"Bootloader header: OK @ 0x{BOOTLOADER:X}")
print(f"Partition table magic: OK @ 0x{PARTITIONS:X}")
print(f"boot_app0 offset reserved: 0x{BOOT_APP0:X}")
print(f"Application header: OK @ 0x{APP:X}")
print(f"SHA256: {hashlib.sha256(data).hexdigest()}")
print("Factory image structural checks passed; physical board flashing is not yet verified.")
