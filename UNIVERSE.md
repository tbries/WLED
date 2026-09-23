## Changes & Notes for GitHub Universe '25 Prep

Changes to the default behavior:
- LED Color is Green on boot (instead of orange)
- LED Brightness is 100% on boot (instead of 50%)
- LED Count is 110 on boot (instead of 30)

These changes are made to provide a more visually appealing demo experience directly out of the box, without requiring any initial configuration by the user.

## Deployment Steps

On Apple Silicon Macs, install Rosetta before building the ESP8266 firmware because PlatformIO's ESP8266 compiler is an Intel executable:

```sh
softwareupdate --install-rosetta --agree-to-license
```

Create and activate a local Python environment, then install PlatformIO and its dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Install the web build dependencies and generate the embedded web assets:

```sh
npm ci
npm run build
```

To flash an [ESP8266](https://www.amazon.com/dp/B0BR9GBNZH?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1) chip connected via USB:
```sh
pio run -e universe_esp8266_2m --target upload
```

To flash an [ESP32](https://www.adafruit.com/product/6160) chip connected via USB:
```sh
pio run -e universe_esp32dev --target upload
```

To list connected devices:
```sh
pio device list
```

Sample output:
```
...
/dev/cu.usbserial-110
---------------------
Hardware ID: USB VID:PID=1A86:7523 LOCATION=1-1
Description: USB Serial

/dev/cu.usbserial-210
---------------------
Hardware ID: USB VID:PID=1A86:7523 LOCATION=2-1
Description: USB Serial
```

To flash to a specific port, add the `--upload-port` flag:
```sh
pio run -e universe_esp8266_2m --target upload --upload-port /dev/cu.usbserial-210
```

## Auto-Flash Script

For demos with multiple devices, use the automated flashing script:
```sh
python3 auto_flash.py
```

This script:
- Builds each supported Universe firmware environment before monitoring begins
- Continuously monitors for new ESP8266/ESP32 devices
- Queries each board's Espressif bootloader to distinguish ESP8266 from ESP32, even when both use the same USB-serial adapter
- Uses explicit `ESP8266` or `ESP32` device descriptions directly when available
- **Erases flash memory before flashing** to ensure clean installations (removes old settings)
- Automatically flashes them with WLED firmware
- Supports ESP8266 and ESP32 flashing simultaneously; devices using the same firmware environment are queued to protect PlatformIO's shared build directory
- Reports success/failure and tells you when devices can be disconnected
- Press Ctrl+C to stop

The first run may take several minutes while PlatformIO downloads packages and builds the firmware targets. If a target cannot be built, the script continues monitoring for device types whose firmware is available. On Apple Silicon without Rosetta, ESP8266 is skipped while ESP32 flashing remains available.

If the script cannot identify a board, put it in download mode and reconnect it. The script will not guess based on a CH340, CP210x, or FTDI adapter because those USB bridges can be connected to either MCU family.

## Sample Images

<div style="display: flex; gap: 10px; align-items: flex-start;">
  <img src="images/PXL_20251014_175258090.jpg" alt="Lamp in green. It's more green IRL." width="400" />
  <img src="images/Screenshot_20251014-104932.png" alt="Example settings page with green color & brightness." width="400" />
</div>
