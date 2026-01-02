# Pi-hole Stats Display

A customized system monitoring display for Raspberry Pi with an ST7789 LCD screen. This script displays real-time system statistics, Pi-hole metrics, and a spinning globe animation with a dark brown and orange command center aesthetic.

## Overview

This is a **modified version** of the original Adafruit Industries stats display example. The original code has been extensively customized with multiple display pages, system monitoring, animated globe visualization, and advanced button controls.

**Original Authors**: Brent Rubell & Mikey Sklar (Adafruit Industries)
**License**: MIT

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- ST7789 RGB LCD Display (240x135 pixels)
- 2 Push buttons (connected to GPIO pins D23 and D24)
- SPI connection for display

## Features

### Three Display Pages

**Page 1 - Pi-hole Stats:**
- IP Address: Local network IP
- Ads Blocked: Total ads blocked by Pi-hole
- Clients: Number of active clients
- CPU Temperature: Real-time temperature with warning color (red if >60°C)

**Page 2 - System Stats:**
- CPU Usage: Current CPU utilization percentage
- Memory: RAM used/total with percentage
- Disk Space: Root partition usage
- Uptime: System uptime

**Page 3 - Spinning Globe:**
- Animated Earth visualization using sprite sheet
- 84-frame continuous rotation animation
- Centered display with black background

### Visual Theme
- Dark brown background `(25, 15, 5)`
- Orange accent colors `(255, 140, 0)`
- Center-aligned layout with border accent corners
- Clean, static displays (no transition animations)

### Button Controls
- **Button A (GPIO D23)**: Cycle through pages (Pi-hole → System → Globe → Pi-hole)
- **Button B (GPIO D24)**: Toggle display on/off
- **Both Buttons (2s hold)**: Initiate system reboot with warning message

## Installation

### 1. Install Dependencies

```bash
# For system-managed Python environments (Raspberry Pi OS Bookworm+)
pip3 install --break-system-packages pillow adafruit-blinka adafruit-circuitpython-rgb-display requests

# OR use a virtual environment (recommended)
python3 -m venv pihole
source pihole/bin/activate
pip install pillow adafruit-blinka adafruit-circuitpython-rgb-display requests
```

### 2. Globe Sprite Sheet

Ensure `earthspin-sheet.png` is in the same directory as `stats.py`:
- **Format**: PNG sprite sheet
- **Dimensions**: 480x480 pixels
- **Frame Size**: 48x48 pixels per frame
- **Layout**: 10 columns × 10 rows (84 frames total)

The script will display an error message on the globe page if the sprite sheet is not found.

### 3. Configure Pi-hole API

The script expects Pi-hole API to be available at:
```
http://localhost/api/stats/summary
```

If your Pi-hole is on a different host, modify the `API_URL` in `stats.py`:
```python
API_URL = "http://your-pihole-ip/api/stats/summary"
```

### 4. Hardware Setup

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

Adjust font sizes (around line 86-87):
```python
font = ImageFont.truetype(FONT_PATH, 16)       # Main data font
font_small = ImageFont.truetype(FONT_PATH, 12) # Header font
```

### Globe Animation Speed

Modify globe rotation speed (around line 110):
```python
GLOBE_FRAME_DELAY = 0.1  # Seconds between frames (0.1 = 10fps)
```

### Reboot Hold Duration

Change the time required to hold both buttons for reboot (around line 105):
```python
REBOOT_HOLD_DURATION = 2.0  # Seconds (default: 2 seconds)
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
- Missing `digitalio` module: Install Adafruit Blinka library

### Globe page shows error message
- Verify `earthspin-sheet.png` exists in the same directory as `stats.py`
- Check sprite sheet dimensions (should be 480x480 pixels)
- Ensure sprite sheet is readable (correct permissions)

### System stats show "N/A"
- Commands may fail on non-Linux systems
- Verify standard utilities are available: `top`, `free`, `df`, `uptime`
- Check that script has permissions to run system commands

### Reboot doesn't work
- Script must run with sudo privileges for reboot command
- Hold both buttons for full 2 seconds
- Check system logs for permission errors

## Files

- `stats.py` - Main display script with three-page cycling display
- `earthspin-sheet.png` - Sprite sheet for spinning globe animation (480x480px, 84 frames)
- `run_stats.sh` - Shell script to activate venv and run stats.py
- `README.md` - This file

## Credits

**Original Code**: Adafruit Industries (Brent Rubell & Mikey Sklar)

**Modifications**:
- Three-page display cycling system (Pi-hole stats, System stats, Spinning globe)
- System monitoring integration (CPU, Memory, Disk, Uptime)
- Animated globe visualization using sprite sheet
- Advanced button controls (page cycling, reboot function)
- Custom theming and centered layout design

## License

MIT License - See original license headers in stats.py
