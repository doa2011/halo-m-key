#!/usr/bin/env python3
"""Validate an ESP32 app-only image for the default 4 MB dual-OTA layout."""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: check_ota_image.py <firmware.bin>")

image = Path(sys.argv[1])
data = image.read_bytes()
max_app_size = 0x140000  # default.csv app0/app1 size: 1,310,720 bytes

if not data:
    raise SystemExit("ERROR: empty firmware image")
if data[0] != 0xE9:
    raise SystemExit(f"ERROR: expected ESP image magic 0xE9, got 0x{data[0]:02X}")
if len(data) > max_app_size:
    raise SystemExit(
        f"ERROR: app image {len(data)} bytes exceeds default OTA slot {max_app_size} bytes"
    )

print(f"ESP32 app image: {image}")
print(f"Size: {len(data)} / {max_app_size} bytes ({len(data) / max_app_size:.1%} of OTA slot)")
print(f"SHA256: {hashlib.sha256(data).hexdigest()}")
print("Image header check passed. Device-side partition compatibility still requires confirmation.")
