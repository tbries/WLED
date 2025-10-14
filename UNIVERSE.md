## Changes & Notes for GitHub Universe '25 Prep

Changes to the default behavior:
- LED Color is Green on boot (instead of orange)
- LED Brightness is 100% on boot (instead of 50%)
- LED Count is 110 on boot (instead of 30)

These changes are made to provide a more visually appealing demo experience directly out of the box, without requiring any initial configuration by the user.

## Deployment Steps
```sh
npm ci
```

```sh
npm run build
```

To flash an [ESP8266](https://www.amazon.com/dp/B0BR9GBNZH?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1) chip connected via USB:
```sh
pio run -e esp8266_2m --target upload 
```

To flash an [ESP32](https://www.adafruit.com/product/6160) chip connected via USB:
```sh
pio run -e esp32dev --target upload
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
pio run -e esp8266_2m --target upload --upload-port /dev/cu.usbserial-210
```

## Auto-Flash Script

For demos with multiple devices, use the automated flashing script:
```sh
python3 auto_flash.py
```

This script:
- Continuously monitors for new ESP8266/ESP32 devices
- Automatically detects device type and uses the correct PlatformIO environment
- Automatically flashes them with WLED firmware
- Supports multiple devices flashing simultaneously
- Reports success/failure and tells you when devices can be disconnected
- Press Ctrl+C to stop

## Sample Images

<div style="display: flex; gap: 10px; align-items: flex-start;">
  <img src="images/PXL_20251014_175258090.jpg" alt="Lamp in green. It's more green IRL." width="400" />
  <img src="images/Screenshot_20251014-104932.png" alt="Example settings page with green color & brightness." width="400" />
</div>
