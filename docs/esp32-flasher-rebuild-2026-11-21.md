# ESP32 flasher baseline rebuild

Rebuild the existing classic ESP32 CC2530 flasher without changing firmware source, GPIO mapping, protocol, partition layout or the pinned upstream revision. Purpose: diagnose repeated 0xFFFF chip ID readings across multiple targets. Verify chip ID before any target erase or write.
