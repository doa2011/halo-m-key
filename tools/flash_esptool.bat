@echo off
setlocal
set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM3"

if not exist "cc2530-flasher-esp32dev-factory.bin" (
  echo ERROR: cc2530-flasher-esp32dev-factory.bin not found in current directory.
  echo Extract the complete GitHub Actions artifact and run this script beside the BIN.
  exit /b 2
)

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher "py" not found.
  echo Install Python, then run: py -m pip install esptool==4.9.0
  exit /b 3
)

echo.
echo Target: classic ESP32, 4 MB flash
echo Serial port: %PORT%
echo This operation ERASES the entire ESP32 flash, including the existing ESPHome firmware,
echo partition table, NVS, Wi-Fi credentials and all stored data.
echo Make sure you have a verified full 4 MB backup before continuing.
echo.
choice /C YN /M "Continue and erase the entire flash"
if errorlevel 2 exit /b 1

py -m esptool --chip esp32 --port "%PORT%" --baud 460800 erase_flash
if errorlevel 1 (
  echo ERROR: erase_flash failed. Check port, cable and ESP32 download mode.
  exit /b 4
)

py -m esptool --chip esp32 --port "%PORT%" --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB 0x0 cc2530-flasher-esp32dev-factory.bin
if errorlevel 1 (
  echo ERROR: factory image write failed. Keep USB connected and inspect esptool output.
  exit /b 5
)

echo.
echo Flash completed. Disconnect/reconnect power, then join Wi-Fi:
echo SSID: ESP32-CC-Flasher
echo Password: 12345678
echo Web: http://192.168.4.1
exit /b 0
