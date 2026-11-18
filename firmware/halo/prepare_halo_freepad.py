#!/usr/bin/env python3
"""Patch the upstream DIYRuZ FreePad 2.0.x source for Halo M-Key V0.6.

The script deliberately modifies source/configuration only. It never fabricates a HEX.
Run from this repository against a clean DIYRuZ/freepad checkout.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_halo_freepad.py <freepad-checkout>")

root = Path(sys.argv[1]).resolve()
required = [
    root / "Source/preinclude.h",
    root / "Source/hal_key.c",
    root / "Source/hal_board_cfg.h",
    root / "Source/zcl_freepadapp_data.c",
    root / "CC2530DB/GenericApp.ewp",
    root / "CC2530DB/GenericApp.eww",
]
for path in required:
    if not path.is_file():
        raise SystemExit(f"Missing upstream FreePad file: {path}")

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one patch anchor, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

# Board selection, six logical endpoints, and power-saving support.
preinclude = root / "Source/preinclude.h"
replace_once(
    preinclude,
    "#if !defined(HAL_BOARD_FREEPAD) && !defined(HAL_BOARD_CHDTECH_DEV) && !defined(HAL_BOARD_LETV)",
    "#if !defined(HAL_BOARD_FREEPAD) && !defined(HAL_BOARD_CHDTECH_DEV) && !defined(HAL_BOARD_LETV) && !defined(HAL_BOARD_HALO_M_KEY)",
)
replace_once(
    preinclude,
    """#if defined(HAL_BOARD_LETV)
    #define FREEPAD_BUTTONS_COUNT 8
#else
    #define FREEPAD_BUTTONS_COUNT 20
#endif""",
    """#if defined(HAL_BOARD_LETV)
    #define FREEPAD_BUTTONS_COUNT 8
#elif defined(HAL_BOARD_HALO_M_KEY)
    #define FREEPAD_BUTTONS_COUNT 6
#else
    #define FREEPAD_BUTTONS_COUNT 20
#endif""",
)
replace_once(
    preinclude,
    "#if defined(HAL_BOARD_FREEPAD) || defined(HAL_BOARD_LETV)",
    "#if defined(HAL_BOARD_FREEPAD) || defined(HAL_BOARD_LETV) || defined(HAL_BOARD_HALO_M_KEY)",
)

# Six independent active-low keys on P1.2..P1.7.
key_c = root / "Source/hal_key.c"
replace_once(
    key_c,
    """#elif defined(HAL_BOARD_LETV)
#define HAL_KEY_P0_GPIO_PINS""",
    """#elif defined(HAL_BOARD_HALO_M_KEY)
#define HAL_KEY_P0_GPIO_PINS 0x00
#define HAL_KEY_P1_GPIO_PINS 0xFC
#define HAL_KEY_P2_GPIO_PINS 0x00
#define HAL_KEY_P0_INPUT_PINS 0x00
#define HAL_KEY_P1_INPUT_PINS 0xFC
#define HAL_KEY_P2_INPUT_PINS 0x00
#define HAL_KEY_P0_INTERRUPT_PINS 0x00
#define HAL_KEY_P1_INTERRUPT_PINS 0xFC
#define HAL_KEY_P2_INTERRUPT_PINS 0x00

#elif defined(HAL_BOARD_LETV)
#define HAL_KEY_P0_GPIO_PINS""",
)
replace_once(
    key_c,
    """#elif defined(HAL_BOARD_CHDTECH_DEV)
    P0DIR &= ~(HAL_KEY_P0_INPUT_PINS);
    P1DIR &= ~(HAL_KEY_P1_INPUT_PINS);
    P2DIR &= ~(HAL_KEY_P2_INPUT_PINS);

#endif""",
    """#elif defined(HAL_BOARD_CHDTECH_DEV)
    P0DIR &= ~(HAL_KEY_P0_INPUT_PINS);
    P1DIR &= ~(HAL_KEY_P1_INPUT_PINS);
    P2DIR &= ~(HAL_KEY_P2_INPUT_PINS);

#elif defined(HAL_BOARD_HALO_M_KEY)
    P1DIR &= ~HAL_KEY_P1_INPUT_PINS;  // P1.2..P1.7 are inputs
    P1INP &= ~HAL_KEY_P1_INPUT_PINS;  // select pull-up/pull-down mode
    P2INP &= ~HAL_KEY_BIT6;           // port 1 inputs use pull-ups

#endif""",
)
replace_once(
    key_c,
    """#elif defined(HAL_BOARD_CHDTECH_DEV)
    PICTL |= HAL_KEY_BIT0 | HAL_KEY_BIT3; // set falling edge on port 0 and 2
    IEN1 |= HAL_KEY_BIT5;                 // enable port0 int
    IEN2 |= HAL_KEY_BIT1;                 // enable port2 int

#endif""",
    """#elif defined(HAL_BOARD_CHDTECH_DEV)
    PICTL |= HAL_KEY_BIT0 | HAL_KEY_BIT3; // set falling edge on port 0 and 2
    IEN1 |= HAL_KEY_BIT5;                 // enable port0 int
    IEN2 |= HAL_KEY_BIT1;                 // enable port2 int

#elif defined(HAL_BOARD_HALO_M_KEY)
    P1INP &= ~HAL_KEY_P1_INPUT_PINS;      // GPIO input with pull resistor
    P2INP &= ~HAL_KEY_BIT6;               // port 1 pull-up
    PICTL |= HAL_KEY_BIT1 | HAL_KEY_BIT2; // falling edge on P1.2..P1.7 (low and high nibbles)
    IEN2 |= HAL_KEY_BIT4;                 // enable port 1 interrupt
    P1IFG &= ~HAL_KEY_P1_INTERRUPT_PINS;
    P1IF = 0;

#endif""",
)
replace_once(
    key_c,
    """#elif defined(HAL_BOARD_CHDTECH_DEV)
    
    if (ACTIVE_LOW(P0 & HAL_KEY_P0_INPUT_PINS)) {
        key = 0x01;
    }

    if (ACTIVE_LOW(P2 & HAL_KEY_P2_INPUT_PINS)) {
        key = 0x02;
    }
 
#endif""",
    """#elif defined(HAL_BOARD_CHDTECH_DEV)
    
    if (ACTIVE_LOW(P0 & HAL_KEY_P0_INPUT_PINS)) {
        key = 0x01;
    }

    if (ACTIVE_LOW(P2 & HAL_KEY_P2_INPUT_PINS)) {
        key = 0x02;
    }

#elif defined(HAL_BOARD_HALO_M_KEY)
    {
        uint8 pressed = (uint8)(~P1) & HAL_KEY_P1_INPUT_PINS;
        /* Accept one key at a time; simultaneous multi-key presses are ignored. */
        if (pressed != 0 && (pressed & (pressed - 1)) == 0) {
            key = pressed; /* P1.2..P1.7: 0x04,0x08,0x10,0x20,0x40,0x80 */
        }
    }
 
#endif""",
)


# Halo M-Key has no LED; provide zero-mask aliases required by shared HAL_BOARD_INIT.
board_cfg = root / "Source/hal_board_cfg.h"
replace_once(
    board_cfg,
    """#elif defined(HAL_BOARD_LETV)
/* 1 - P1_0 Red */""",
    """#elif defined(HAL_BOARD_HALO_M_KEY)
/* No physical LEDs on Halo M-Key. Keep dummy aliases for common HAL init;
 * LED bit masks are zero, so no GPIO is switched to output. */
  #define LED1_BV           0x00
  #define LED1_SBIT         P0_0
  #define LED1_DDR          P0DIR
  #define LED1_POLARITY     ACTIVE_HIGH
  #define LED2_BV           0x00
  #define LED2_SBIT         P0_0
  #define LED2_DDR          P0DIR
  #define LED2_POLARITY     ACTIVE_HIGH

#elif defined(HAL_BOARD_LETV)
/* 1 - P1_0 Red */""",
)

# Translate the measured P1 bit mask to FreePad logical endpoint numbers.
data_c = root / "Source/zcl_freepadapp_data.c"
replace_once(
    data_c,
    """#elif defined(HAL_BOARD_LETV)
    case 0x1: // 1""",
    """#elif defined(HAL_BOARD_HALO_M_KEY)
    case 0x04: return 1; // S1: P1.2, CC2530 QFN40 pin 8
    case 0x08: return 2; // S2: P1.3, CC2530 QFN40 pin 7
    case 0x10: return 3; // S3: P1.4, CC2530 QFN40 pin 6
    case 0x20: return 4; // S4: P1.5, CC2530 QFN40 pin 5
    case 0x40: return 5; // S5: P1.6, CC2530 QFN40 pin 38
    case 0x80: return 6; // S6: P1.7, CC2530 QFN40 pin 37
#elif defined(HAL_BOARD_LETV)
    case 0x1: // 1""",
)

# Re-purpose the upstream no-Touchlink PM3 configuration for this board.
ewp = root / "CC2530DB/GenericApp.ewp"
project = ewp.read_text(encoding="utf-8")
pattern = re.compile(
    r"(<configuration>\s*<name>DIYRuZ_FreePad_PM3</name>.*?</configuration>)",
    re.DOTALL,
)
matches = list(pattern.finditer(project))
if len(matches) != 1:
    raise SystemExit(f"{ewp}: expected exactly one DIYRuZ_FreePad_PM3 config, found {len(matches)}")
block = matches[0].group(1)
if block.count("<state>HAL_BOARD_FREEPAD</state>") != 1:
    raise SystemExit("PM3 configuration does not contain exactly one HAL_BOARD_FREEPAD define")
block = block.replace("<name>DIYRuZ_FreePad_PM3</name>", "<name>HALO_M_KEY_PM3</name>", 1)
block = block.replace("<state>HAL_BOARD_FREEPAD</state>", "<state>HAL_BOARD_HALO_M_KEY</state>", 1)
block = block.replace("DIYRuZ_FreePad_PM3", "HALO_M_KEY_PM3")
project = project[:matches[0].start()] + block + project[matches[0].end():]
ewp.write_text(project, encoding="utf-8")

eww = root / "CC2530DB/GenericApp.eww"
replace_once(
    eww,
    "<configuration>DIYRuZ_FreePad_PM3</configuration>",
    "<configuration>HALO_M_KEY_PM3</configuration>",
)

# Guard against accidental changes to the selected board profile.
assert "HAL_BOARD_HALO_M_KEY" in (root / "Source/preinclude.h").read_text(encoding="utf-8")
assert "FREEPAD_BUTTONS_COUNT 6" in (root / "Source/preinclude.h").read_text(encoding="utf-8")
assert "0xFC" in key_c.read_text(encoding="utf-8")
print("Halo M-Key source adaptation applied.")
print("Board: HALO_M_KEY; buttons: 6; keys: active-low P1.2..P1.7")
print("IAR configuration: HALO_M_KEY_PM3 (PM3, no Touchlink, no LED hardware)")
print("No HEX was generated by this patch step; build with licensed IAR 8051 + TI Z-Stack 3.0.2.")
