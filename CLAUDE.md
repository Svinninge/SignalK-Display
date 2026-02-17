# CLAUDE.md - SignalK-Display

## Project Overview

SignalK-Display is a Python 3 application for Raspberry Pi that reads marine vessel data from a [Signal K](http://signalk.org) server and renders it on a Waveshare 2.7" e-Paper HAT (black/red dual-color display). It is designed for embedded, always-on use aboard boats.

**Target hardware:** Raspberry Pi 3 (also supports Jetson Nano) with Waveshare 2.7" e-Paper HAT, Ruuvi Bluetooth sensor, and GPS connected to Signal K.

## Repository Structure

```
SignalK-Display/
├── SignalK.py              # Main application - Signal K client, display logic, entry point
├── Waveshare/
│   ├── epd2in7b.py         # Low-level e-Paper display driver (Waveshare 2.7" B)
│   └── epdconfig.py        # Hardware abstraction layer (Raspberry Pi / Jetson Nano)
├── README.md               # Project description
├── LICENSE                  # GPLv3
└── CLAUDE.md               # This file
```

Total codebase: ~650 lines of Python across 3 source files.

## Architecture

The application uses a layered architecture:

1. **Application layer** (`SignalK.py` main block, line 162+) — Orchestrates data fetching and display rendering.
2. **Service classes** (`SignalK.py`) — `SignalK` class wraps the Signal K REST API; `Display` class wraps e-Paper rendering.
3. **Display driver** (`Waveshare/epd2in7b.py`) — Low-level SPI commands for the 176x264 pixel dual-color e-Paper.
4. **Hardware abstraction** (`Waveshare/epdconfig.py`) — Runtime platform detection (RPi vs Jetson Nano), GPIO/SPI interface.

### Key classes and functions

- **`SignalK`** (`SignalK.py:96`) — HTTP client for Signal K server. Constructor takes server URL. `Read_SignalK()` fetches and parses JSON from API endpoints.
- **`Display`** (`SignalK.py:56`) — Initializes e-Paper and renders 5 rows of text (black + red layers). Uses PIL/Pillow for image composition.
- **`get_interface()`** (`SignalK.py:26`) — Retrieves network interface info (eth0/wlan0 IP and SSID).
- **`get_CPUtemp()`** (`SignalK.py:132`) — Reads CPU temperature via `gpiozero`.
- **`get_IP()`** (`SignalK.py:137`) — Gets internal/external IP addresses.

### Data flow

1. Fetch CPU temperature and network info
2. Connect to Signal K server at `http://127.0.0.1:3000`
3. Read vessel MMSI, refrigerator temperature (Kelvin → Celsius), barometric pressure, GPS position
4. Apply alert rules (red highlight if CPU >60°C or fridge temp out of 0–8°C range)
5. Render 5-row display: boat name, network info, temperatures, GPS coordinates, pressure + timestamp

## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client for Signal K REST API |
| `Pillow` (PIL) | Image creation and text rendering for display |
| `gpiozero` | CPU temperature reading and button input |
| `pytemperature` | Kelvin-to-Celsius conversion |
| `spidev` | SPI bus communication with e-Paper |
| `RPi.GPIO` | GPIO pin control (Raspberry Pi) |

Install with:
```bash
sudo pip3 install requests Pillow gpiozero pytemperature spidev RPi.GPIO
```

There is no `requirements.txt`, `setup.py`, or `pyproject.toml`.

## Running the Application

```bash
python3 SignalK.py
```

The script expects:
- A Signal K server running at `http://127.0.0.1:3000`
- The Waveshare 2.7" e-Paper HAT connected via SPI
- FreeSerif font installed at `/usr/share/fonts/truetype/freefont/FreeSerif.ttf`
- The Waveshare module path hardcoded to `/home/pi/Documents/SignalK-Display/Waveshare/` (line 6)

## Development Notes

### No build system
This is a standalone Python script — no compilation, bundling, or build steps.

### No tests
There are no unit tests, integration tests, or test framework configured.

### No linting/formatting
No flake8, pylint, black, or other tool configuration exists.

### No CI/CD
No GitHub Actions, GitLab CI, or other automation pipelines.

### Code conventions observed in this codebase
- Python 3 with `#!/usr/bin/python3` shebang
- ISO-8859-15 file encoding (Scandinavian character support)
- f-strings for string formatting
- `print()` statements used for debug output
- Temperature values from Signal K are in Kelvin; convert to Celsius using `pytemperature.k2c()`
- Pressure values are in Pascals from Signal K; converted to mmHg for display
- GPS coordinates are accessed as `latitude`/`longitude` keys from JSON response
- Module-level code executes at import time (lines 52–54 call `get_interface()`)

### Important caveats
- The `sys.path.append` on line 6 uses an absolute path (`/home/pi/Documents/...`) — this must match the deployment location.
- The `get_ip_address()` function (line 18) is effectively unused/deprecated; `get_IP()` is used instead.
- The `handleBtnPress()` method is a stub with no implementation.
- `.pyc` files are committed to the repository.

## Signal K API Endpoints Used

All endpoints are relative to the Signal K server base URL:

- `/signalk/v1/api/vessels/` — List vessels (first result is own ship)
- `/signalk/v1/api/vessels/{mmsi}/environment/inside/refrigerator/temperature/value` — Fridge temp (Kelvin)
- `/signalk/v1/api/vessels/{mmsi}/environment/inside/refrigerator/pressure/value` — Pressure (Pascals)
- `/signalk/v1/api/vessels/{mmsi}/navigation/position/value/` — GPS position (lat/lon)

## Display Layout

The e-Paper renders 5 rows on a 176x264 pixel display:

| Row | Font Size | Color | Content |
|-----|-----------|-------|---------|
| 1 | Large (30pt) | Red | Boat name |
| 2 | Small (14pt) | Black | Network interfaces (eth0 + wlan0) |
| 3 | Medium (22pt) | Red or Black* | Fridge temp + CPU temp |
| 4 | Medium (22pt) | Black | GPS position |
| 5 | Medium (22pt) | Black | Barometric pressure |
| Footer | Medium (22pt) | Black | Current timestamp |

*Row 3 turns red when temperatures are out of normal range.
