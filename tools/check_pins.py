#!/usr/bin/env python3
"""对现场实测的 CC2530 Halo 六键记录进行独立一致性检查。"""
import csv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / 'hardware/pins.csv').open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

expected = [
    ('S1', 8, 'P1.2', 0x04),
    ('S2', 7, 'P1.3', 0x08),
    ('S3', 6, 'P1.4', 0x10),
    ('S4', 5, 'P1.5', 0x20),
    ('S5', 38, 'P1.6', 0x40),
    ('S6', 37, 'P1.7', 0x80),
]

assert len(rows) == len(expected), f'按键数量错误：{len(rows)}'
header = (root / 'firmware/halo/HALO_M_KEY_GPIO.h').read_text(encoding='utf-8')
assert '#define HALO_KEY_MASK 0xFCu' in header
for row, (button, pin, gpio, mask) in zip(rows, expected):
    actual = (
        row['button'], int(row['cc2530_pin']), row['gpio'],
        row['active_level'].upper(), int(row['mask'], 16),
    )
    assert actual == (button, pin, gpio, 'LOW', mask), row
    bit = int(gpio.split('.')[1])
    assert f'#define HALO_{button}_BIT (1u << {bit})' in header, button

assert sum(item[3] for item in expected) == 0xFC
print('PASS: 6 keys P1.2-P1.7, active-low, mask=0xFC')
