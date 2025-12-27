# Pi-hole Stats Display

A customized system monitoring display for Raspberry Pi with an ST7789 LCD screen. This script displays real-time system statistics and Pi-hole metrics with a dark brown and orange command center aesthetic.

## Overview

This is a **modified version** of the original Adafruit Industries stats display example. The original code has been extensively customized with new visual themes, animations, and user interactions.

**Original Authors**: Brent Rubell & Mikey Sklar (Adafruit Industries)
**License**: MIT

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- ST7789 RGB LCD Display (240x135 pixels)
- 2 Push buttons (connected to GPIO pins D23 and D24)
- SPI connection for display

## Features

### Display Information
- **IP Address**: Local network IP
- **Ads Blocked**: Total ads blocked by Pi-hole
- **Clients**: Number of active clients
- **CPU Temperature**: Real-time temperature with warning color (red if >60°C)

### Visual Theme
- Dark brown background `(25, 15, 5)`
- Orange accent colors `(255, 140, 0)`
- Center-aligned layout
- Border accent corners
- Animated startup sequence

### Button Controls
- **Button A (GPIO D23)**: Trigger animated data reveal
- **Button B (GPIO D24)**: Toggle display on/off

### Animations
- **Standby Screen**: Blinking "PRESS BTN A TO INITIALIZE" with corner brackets
- **Startup Sequence**: Data grows from center (30% to 100% scale over ~2 seconds)
- **Static Display**: Clean centered layout with all metrics

## Installation

### 1. Install Dependencies

```bash
# Activate your virtual environment
source pihole/bin/activate

# Install required packages
pip install pillow adafruit-blinka adafruit-circuitpython-rgb-display requests
```

### 2. Configure Pi-hole API

The script expects Pi-hole API to be available at:
```
http://localhost/api/stats/summary
```

If your Pi-hole is on a different host, modify the `API_URL` in `stats.py`:
```python
API_URL = "http://your-pihole-ip/api/stats/summary"
```

### 3. Hardware Setup

Connect the ST7789 display:
- **CS**: GPIO 17 (board.D17)
- **DC**: GPIO 25 (board.D25)
- **SPI**: Hardware SPI pins

Connect buttons:
- **Button A**: GPIO 23 (board.D23)
- **Button B**: GPIO 24 (board.D24)

## Usage

### Manual Start

```bash
# Run directly
source pihole/bin/activate
python stats.py
```

### Using the Shell Script

```bash
# Make executable (first time only)
chmod +x run_stats.sh

# Run the script
./run_stats.sh
```

### Run as Background Service

```bash
# Start in background with nohup
nohup ./run_stats.sh > /tmp/stats.log 2>&1 &

# Check if running
ps aux | grep stats.py

# View logs
tail -f /tmp/stats.log
```

### Auto-start on Boot

Add to crontab:
```bash
crontab -e
```

Add this line:
```
@reboot /path/to/run_stats.sh >> /tmp/stats.log 2>&1
```

## Configuration

### Display Rotation

The display is currently set to 270° rotation. To change:
```python
rotation=270  # Options: 0, 90, 180, 270
```

### Colors

Customize the color palette (lines 105-111 in stats.py):
```python
COLOR_BG = (25, 15, 5)        # Dark brown background
COLOR_ACCENT = (255, 140, 0)   # Orange accent
COLOR_TEXT = (255, 160, 50)    # Orange text
COLOR_WARN = (255, 50, 50)     # Red warning (high temp)
```

### Font Size

Adjust font sizes (lines 86-87):
```python
font = ImageFont.truetype(FONT_PATH, 16)       # Main data font
font_small = ImageFont.truetype(FONT_PATH, 12) # Header font
```

### Animation Speed

Modify animation duration (line 203):
```python
if frame < 20:  # Change 20 to adjust animation length
```

## Troubleshooting

### Display shows white screen
- Check SPI connections
- Verify CS and DC pin assignments
- Reduce animation complexity if CPU is overloaded

### No Pi-hole data showing
- Verify Pi-hole API is accessible: `curl http://localhost/api/stats/summary`
- Check API_URL configuration
- Look for "N/A" values indicating API errors

### Buttons not responding
- Verify GPIO pin numbers match your hardware
- Check button wiring (pull-up/pull-down resistors)
- Test button state: buttons are active LOW (pressed = False)

### Script crashes on startup
- Check all dependencies are installed
- Verify font path exists: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- Run directly (not via nohup) to see error messages

## Files

- `stats.py` - Main display script
- `run_stats.sh` - Shell script to activate venv and run stats.py
- `README.md` - This file

## Credits

**Original Code**: Adafruit Industries (Brent Rubell & Mikey Sklar)
**Modifications**: Custom animations, theming, button controls, centered layout

## License

MIT License - See original license headers in stats.py
