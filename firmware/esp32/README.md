# ESP32 烧录器

计划使用 https://github.com/z9m/ESP32-CC-Tool-Pro 。当前不存放上游源码或虚构构建成功结果。

已知风险：ESP32-WROOM 的 GPIO6 常用于片上 SPI Flash，不能盲目沿用示例中的 RESET=GPIO6。此前建议的 18/19/21 也仅是候选，需检查 ESP32_MOS_X4 板级走线/占用。确认后引入真实源代码、添加 `platformio.ini` 与自动构建工作流。
