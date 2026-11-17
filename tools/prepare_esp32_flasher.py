#!/usr/bin/env python3
"""Apply the tracked ESP32_MOS_X4 adaptation to the pinned upstream flasher."""
from pathlib import Path
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_esp32_flasher.py <upstream-checkout>")

root = Path(__file__).resolve().parents[1]
upstream = Path(sys.argv[1]).resolve()
main_cpp = upstream / "src" / "main.cpp"
web_index = upstream / "src" / "web_index.h"
web_js = upstream / "src" / "web_js.h"

def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one patch anchor, found {count}: {old[:100]!r}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

replace_once(
    main_cpp,
    '#include <Preferences.h> \n',
    '#include <Preferences.h>\n#include <ArduinoOTA.h>\n',
)
replace_once(
    main_cpp,
    '#define PIN_CC_CLK  4  // for m5stack atom s3 change this to pin 7 as pin 4 isn\'t usable\n#define PIN_CC_DATA 5\n#define PIN_CC_RST  6',
    '#define PIN_CC_CLK  18  // ESP32_MOS_X4 temporary flasher mapping\n#define PIN_CC_DATA 19\n#define PIN_CC_RST  21  // GPIO16/D16 and GPIO17/D17 are intentionally untouched',
)
replace_once(
    main_cpp,
    '    MDNS.begin("cc-tool");',
    '''    MDNS.begin("cc-tool");

    // Independent ArduinoOTA service for future wireless updates.
    ArduinoOTA.setHostname("cc-tool");
    String otaPassword = preferences.getString("ota_pass", ap_password);
    ArduinoOTA.setPassword(otaPassword.c_str());
    ArduinoOTA.onStart([]() { Serial.println("ESP32 OTA update started"); });
    ArduinoOTA.onEnd([]() { Serial.println("\\nESP32 OTA update finished"); });
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        Serial.printf("ESP32 OTA: %u%%\\r", (progress * 100U) / total);
    });
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("ESP32 OTA error: %u\\n", static_cast<unsigned int>(error));
    });
    ArduinoOTA.begin();'''
)
replace_once(
    main_cpp,
    '    server.on("/api/init", HTTP_GET, [](AsyncWebServerRequest *request){',
    '''    server.on("/api/save_ota_password", HTTP_POST, [](AsyncWebServerRequest *r){
        if(!r->hasParam("password", true)) {
            r->send(400, "text/plain", "Missing password");
            return;
        }
        String new_password = r->getParam("password", true)->value();
        if(new_password.length() < 8 || new_password.length() > 64) {
            r->send(400, "text/plain", "Password must be 8-64 characters");
            return;
        }
        preferences.putString("ota_pass", new_password);
        r->send(200, "text/plain", "OTA password saved. Restarting...");
        delay(500);
        ESP.restart();
    });

    server.on("/api/init", HTTP_GET, [](AsyncWebServerRequest *request){'''
)
replace_once(
    main_cpp,
    'void loop() { delay(100); }',
    'void loop() { ArduinoOTA.handle(); delay(10); }',
)

replace_once(
    web_index,
    '''        <div class="card">
            <h2 data-i18n="sec_fw">3. Firmware Update</h2>''',
    '''        <div class="card">
            <h2>ESP32 OTA Password</h2>
            <div style="font-size:0.8rem; color:#888; margin-bottom:12px;">
                Set the password used by PlatformIO wireless updates (8-64 characters).
            </div>
            <div class="btn-group">
                <input type="password" id="otaPassword" placeholder="New OTA password (min 8 chars)" style="background:#111; border:1px solid #444; color:#fff; padding:10px; border-radius:4px; font-family:inherit; font-size:0.85rem;">
                <button class="primary" onclick="saveOtaPassword()">SAVE OTA PASSWORD</button>
            </div>
        </div>

        <div class="card">
            <h2 data-i18n="sec_fw">3. Firmware Update</h2>'''
)
replace_once(
    web_js,
    '  function loadWifiInfo() {',
    '''  function saveOtaPassword() {
    const password = document.getElementById('otaPassword').value;
    if(password.length < 8 || password.length > 64) {
      log("OTA: password must be 8-64 characters.");
      return;
    }
    const body = new URLSearchParams({ password });
    fetch('/api/save_ota_password', { method: 'POST', body })
      .then(r => r.text()).then(t => log("OTA: " + t))
      .catch(e => log("OTA password error: " + e));
  }

  function loadWifiInfo() {'''
)

shutil.copy2(root / "firmware" / "esp32" / "platformio.ini", upstream / "platformio.ini")

patched = main_cpp.read_text(encoding="utf-8")
for forbidden in ("#define PIN_CC_CLK  16", "#define PIN_CC_DATA 16", "#define PIN_CC_RST  16",
                  "#define PIN_CC_CLK  17", "#define PIN_CC_DATA 17", "#define PIN_CC_RST  17"):
    if forbidden in patched:
        raise SystemExit(f"Forbidden GPIO16/17 assignment detected: {forbidden}")

print("Prepared ESP32_MOS_X4 flasher: DC=18, DD=19, RESET=21")
print("GPIO16/D16 and GPIO17/D17 are not configured")
print("ArduinoOTA enabled; default password 12345678 (change in web UI)")
