#!/usr/bin/env python3
"""Static acceptance checks for the patched FreePad/Halo M-Key source tree."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: check_halo_port.py <patched-freepad-checkout>")
root = Path(sys.argv[1]).resolve()
pre = (root / "Source/preinclude.h").read_text(encoding="utf-8")
key = (root / "Source/hal_key.c").read_text(encoding="utf-8")
data = (root / "Source/zcl_freepadapp_data.c").read_text(encoding="utf-8")
ewp = (root / "CC2530DB/GenericApp.ewp").read_text(encoding="utf-8")
eww = (root / "CC2530DB/GenericApp.eww").read_text(encoding="utf-8")

checks = {
    "six logical endpoints": "FREEPAD_BUTTONS_COUNT 6" in pre,
    "PM3 power-saving enabled": "HAL_BOARD_HALO_M_KEY)" in pre and "POWER_SAVING" in pre,
    "P1.2-P1.7 mask": "#define HAL_KEY_P1_INPUT_PINS 0xFC" in key,
    "P1 port interrupt enabled": "IEN2 |= HAL_KEY_BIT4" in key,
    "falling-edge wake": "PICTL |= HAL_KEY_BIT1" in key,
    "active-low sampling": "(uint8)(~P1) & HAL_KEY_P1_INPUT_PINS" in key,
    "S1..S6 endpoint map": all(f"case 0x{m:02X}: return {i};" in data for i, m in enumerate((4,8,16,32,64,128),1)),
    "IAR PM3 profile": "<name>HALO_M_KEY_PM3</name>" in ewp,
    "IAR board define": "<state>HAL_BOARD_HALO_M_KEY</state>" in ewp,
    "workspace profile": "<configuration>HALO_M_KEY_PM3</configuration>" in eww,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + " " + name)
if failed:
    raise SystemExit("Halo source checks failed: " + ", ".join(failed))
print("All static source checks passed. This is not a compiler/HEX validation.")
