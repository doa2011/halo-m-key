@echo off
setlocal
set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM3"

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher "py" not found.
  echo Install Python, then run: py -m pip install esptool==4.9.0
  exit /b 2
)

echo.
echo This reads (does NOT erase or write) the full 4 MB ESP32 flash twice.
echo Target: classic ESP32, 4 MB flash; serial port: %PORT%
echo Disconnect UART0 peripherals from GPIO1/GPIO3 before entering download mode.
echo.
choice /C YN /M "Read and verify the original 4 MB flash"
if errorlevel 2 exit /b 1

py -m esptool --chip esp32 --port "%PORT%" --baud 460800 read_flash 0x0 0x400000 esp32-mos-x4-original-4mb-1.bin
if errorlevel 1 exit /b 3

py -m esptool --chip esp32 --port "%PORT%" --baud 460800 read_flash 0x0 0x400000 esp32-mos-x4-original-4mb-2.bin
if errorlevel 1 exit /b 4

fc /b esp32-mos-x4-original-4mb-1.bin esp32-mos-x4-original-4mb-2.bin >nul
if errorlevel 1 (
  echo ERROR: The two reads differ. Do not erase or flash yet.
  echo Check power, cable, serial speed and wiring, then repeat the backup.
  exit /b 5
)

echo.
echo Both 4 MB reads are identical.
certutil -hashfile esp32-mos-x4-original-4mb-1.bin SHA256
echo Keep both backup files in a safe location before flashing.
exit /b 0
