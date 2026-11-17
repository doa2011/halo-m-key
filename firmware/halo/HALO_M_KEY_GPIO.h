#ifndef HALO_M_KEY_GPIO_H
#define HALO_M_KEY_GPIO_H
/* Halo M-Key V0.6, TI CC2530 QFN40
 * Measured by owner: all buttons short to GND when pressed.
 * This file is a hardware map ONLY. It is NOT a flashable firmware.
 */
#define HALO_KEY_MASK 0xFCu
#define HALO_S1_BIT (1u << 2)  /* P1.2, QFN pin 8 */
#define HALO_S2_BIT (1u << 3)  /* P1.3, QFN pin 7 */
#define HALO_S3_BIT (1u << 4)  /* P1.4, QFN pin 6 */
#define HALO_S4_BIT (1u << 5)  /* P1.5, QFN pin 5 */
#define HALO_S5_BIT (1u << 6)  /* P1.6, QFN pin 38 */
#define HALO_S6_BIT (1u << 7)  /* P1.7, QFN pin 37 */
/* Active-low GPIO sampling. CC2530 header defines P1 register. */
#define HALO_KEYS_PRESSED() ((unsigned char)((~P1) & HALO_KEY_MASK))
#endif
