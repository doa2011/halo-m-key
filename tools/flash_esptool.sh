#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-/dev/ttyUSB0}"
IMAGE="cc2530-flasher-esp32dev-factory.bin"

if [[ ! -f "$IMAGE" ]]; then
  echo "ERROR: $IMAGE not found. Extract the complete Actions artifact and run beside the BIN." >&2
  exit 2
fi

if ! python3 -m esptool version >/dev/null 2>&1; then
  echo "Install esptool first: python3 -m pip install esptool==4.9.0" >&2
  exit 3
fi

echo "Target: classic ESP32, 4 MB flash; serial port: $PORT"
echo "WARNING: this erases the entire flash, including ESPHome, partition table, NVS and stored data."
read -r -p "Have you made and verified a full 4 MB backup? Type YES to continue: " CONFIRM
[[ "$CONFIRM" == "YES" ]] || { echo "Cancelled."; exit 1; }

python3 -m esptool --chip esp32 --port "$PORT" --baud 460800 erase_flash
python3 -m esptool --chip esp32 --port "$PORT" --baud 460800 \
  --before default_reset --after hard_reset write_flash \
  --flash_mode dio --flash_freq 40m --flash_size 4MB \
  0x0 "$IMAGE"

echo "Flash complete. AP: ESP32-CC-Flasher / 12345678; web: http://192.168.4.1"
