# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
# SPDX-FileCopyrightText: 2025 Mikey Sklar for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Copyright (c) 2017 Adafruit Industries
# Author: Brent Rubell, Mikey Sklar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!


# -*- coding: utf-8 -*-
# Import Python System Libraries
import time
import json
import subprocess
import random

# Import Requests Library
import requests

#Import Blinka
import digitalio
import board

# Import Python Imaging Library
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

API_URL = "http://localhost/api/stats/summary"

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D17)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    dc_pin,
    cs_pin,
    reset_pin,
    135,
    240,
    baudrate=BAUDRATE,
    x_offset=53,
    y_offset=40,
    rotation=270
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
CANVAS_WIDTH  = disp.height
CANVAS_HEIGHT = disp.width
image = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT))
draw = ImageDraw.Draw(image)

# Load default font (or replace with a TTF if desired)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(FONT_PATH, 16)  # Main data font
font_small = ImageFont.truetype(FONT_PATH, 12)  # Header font

# Load globe sprite sheet
try:
    globe_spritesheet = Image.open("earthspin-sheet.png")
    GLOBE_FRAME_WIDTH = 48  # Each frame is 48x48 pixels
    GLOBE_FRAME_HEIGHT = 48
    GLOBE_FRAMES_PER_ROW = 10
    GLOBE_TOTAL_FRAMES = 84  # Total frames in sprite sheet
except Exception as e:
    print(f"Failed to load globe sprite: {e}")
    globe_spritesheet = None

buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input()

buttonB = digitalio.DigitalInOut(board.D24)
buttonB.switch_to_input()

# Track display state and button state for toggle detection
display_on = True
buttonB_was_pressed = False
buttonA_was_pressed = False

# Display mode tracking
display_mode = "pihole"  # "pihole", "system", or "globe"

# Both buttons hold detection
both_buttons_hold_start = None
REBOOT_HOLD_DURATION = 2.0  # 2 seconds

# Globe animation tracking
globe_frame = 0
globe_last_update = 0
GLOBE_FRAME_DELAY = 0.1  # seconds between frames

# Color palette - Dark brown and orange theme
COLOR_BG = (25, 15, 5)  # Dark brown background
COLOR_GRID = (60, 40, 20)  # Brown grid
COLOR_ACCENT = (255, 140, 0)  # Orange accent
COLOR_TEXT = (255, 160, 50)  # Orange text
COLOR_WARN = (255, 50, 50)  # Red warning
COLOR_GREEN = (255, 180, 80)  # Light orange status

def draw_grid_background(draw, frame):
    """Draw simple static grid background (optimized)"""
    # Static grid - no animation to reduce CPU load
    # Vertical lines
    for x in range(0, CANVAS_WIDTH, 30):
        draw.line([(x, 0), (x, CANVAS_HEIGHT)], fill=COLOR_GRID, width=1)
    # Horizontal lines
    for y in range(0, CANVAS_HEIGHT, 30):
        draw.line([(0, y), (CANVAS_WIDTH, y)], fill=COLOR_GRID, width=1)

def draw_border_accent(draw):
    """Draw NGE-style corner accents"""
    accent_len = 20
    # Top left
    draw.line([(0, 0), (accent_len, 0)], fill=COLOR_ACCENT, width=2)
    draw.line([(0, 0), (0, accent_len)], fill=COLOR_ACCENT, width=2)
    # Top right
    draw.line([(CANVAS_WIDTH - accent_len, 0), (CANVAS_WIDTH, 0)], fill=COLOR_ACCENT, width=2)
    draw.line([(CANVAS_WIDTH - 1, 0), (CANVAS_WIDTH - 1, accent_len)], fill=COLOR_ACCENT, width=2)
    # Bottom left
    draw.line([(0, CANVAS_HEIGHT - 1), (accent_len, CANVAS_HEIGHT - 1)], fill=COLOR_ACCENT, width=2)
    draw.line([(0, CANVAS_HEIGHT - accent_len), (0, CANVAS_HEIGHT)], fill=COLOR_ACCENT, width=2)
    # Bottom right
    draw.line([(CANVAS_WIDTH - accent_len, CANVAS_HEIGHT - 1), (CANVAS_WIDTH, CANVAS_HEIGHT - 1)], fill=COLOR_ACCENT, width=2)
    draw.line([(CANVAS_WIDTH - 1, CANVAS_HEIGHT - accent_len), (CANVAS_WIDTH - 1, CANVAS_HEIGHT)], fill=COLOR_ACCENT, width=2)

def draw_data_row(draw, font, label, value, y_pos, color):
    """Draw a full-width data row"""
    x = 8
    # Draw label
    draw.text((x, y_pos), label + ":", font=font, fill=color)

    # Draw value on same line
    label_width = draw.textbbox((0, 0), label + ": ", font=font)[2]
    draw.text((x + label_width, y_pos), str(value), font=font, fill=COLOR_TEXT)

def draw_static_display(draw, font, ip, ads_blocked, clients, cpu_temp):
    """Draw the static data display"""
    # Border accents
    draw_border_accent(draw)

    # Header
    draw.text((8, 4), "SYSTEM MONITOR", font=font_small, fill=COLOR_ACCENT)
    draw.line([(5, 22), (CANVAS_WIDTH - 5, 22)], fill=COLOR_ACCENT, width=1)

    # Data rows with better spacing
    y_start = 28
    line_height = 28

    # Temperature color
    try:
        temp_val = float(cpu_temp.replace('°C', ''))
        temp_color = COLOR_WARN if temp_val > 60 else COLOR_ACCENT
    except:
        temp_color = COLOR_ACCENT

    # Draw all data
    draw_data_row(draw, font, "IP ADDRESS", ip, y_start, COLOR_ACCENT)
    draw_data_row(draw, font, "ADS BLOCKED", str(ads_blocked), y_start + line_height, COLOR_ACCENT)
    draw_data_row(draw, font, "CLIENTS", str(clients), y_start + line_height * 2, COLOR_ACCENT)
    draw_data_row(draw, font, "CPU TEMP", cpu_temp, y_start + line_height * 3, temp_color)

def get_system_stats():
    """Gather system statistics: CPU, Memory, Disk, Uptime"""
    stats = {}

    try:
        # CPU Usage - parse from top command
        cmd = "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1\"%\"}'"
        stats['cpu'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except:
        stats['cpu'] = "N/A"

    try:
        # Memory Usage - use free command
        cmd = "free -m | awk 'NR==2{printf \"%.0f/%.0fMB (%.0f%%)\", $3,$2,$3*100/$2 }'"
        stats['memory'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except:
        stats['memory'] = "N/A"

    try:
        # Disk Space - root partition
        cmd = "df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'"
        stats['disk'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except:
        stats['disk'] = "N/A"

    try:
        # Uptime - formatted
        cmd = "uptime -p | sed 's/up //'"
        stats['uptime'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except:
        stats['uptime'] = "N/A"

    return stats

def draw_system_stats_display(draw, font, stats):
    """Draw the system stats display"""
    # Border accents
    draw_border_accent(draw)

    # Header
    draw.text((8, 4), "SYSTEM STATS", font=font_small, fill=COLOR_ACCENT)
    draw.line([(5, 22), (CANVAS_WIDTH - 5, 22)], fill=COLOR_ACCENT, width=1)

    # Data rows with better spacing
    y_start = 28
    line_height = 28

    # Draw all system stats
    draw_data_row(draw, font, "CPU USAGE", stats.get('cpu', 'N/A'), y_start, COLOR_ACCENT)
    draw_data_row(draw, font, "MEMORY", stats.get('memory', 'N/A'), y_start + line_height, COLOR_ACCENT)
    draw_data_row(draw, font, "DISK", stats.get('disk', 'N/A'), y_start + line_height * 2, COLOR_ACCENT)
    draw_data_row(draw, font, "UPTIME", stats.get('uptime', 'N/A'), y_start + line_height * 3, COLOR_ACCENT)

def draw_globe_animation(spritesheet, frame_number):
    """Draw the spinning globe animation from sprite sheet"""
    if spritesheet is None:
        # Fallback: create error image
        error_img = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG)
        error_draw = ImageDraw.Draw(error_img)
        error_draw.text((20, CANVAS_HEIGHT // 2), "Globe sprite not found", font=font, fill=COLOR_WARN)
        return error_img, 0, 0

    # Calculate which frame to extract from sprite sheet
    row = frame_number // GLOBE_FRAMES_PER_ROW
    col = frame_number % GLOBE_FRAMES_PER_ROW

    # Extract the frame from sprite sheet
    left = col * GLOBE_FRAME_WIDTH
    top = row * GLOBE_FRAME_HEIGHT
    right = left + GLOBE_FRAME_WIDTH
    bottom = top + GLOBE_FRAME_HEIGHT

    globe_frame = spritesheet.crop((left, top, right, bottom))

    # Scale to fit display nicely (center it and make it large)
    scale_factor = min(CANVAS_WIDTH, CANVAS_HEIGHT) / GLOBE_FRAME_WIDTH * 0.8
    new_size = (int(GLOBE_FRAME_WIDTH * scale_factor), int(GLOBE_FRAME_HEIGHT * scale_factor))
    globe_frame = globe_frame.resize(new_size, Image.Resampling.LANCZOS)

    # Convert to RGB if needed
    if globe_frame.mode != 'RGB':
        globe_frame = globe_frame.convert('RGB')

    # Calculate center position
    x_pos = (CANVAS_WIDTH - new_size[0]) // 2
    y_pos = (CANVAS_HEIGHT - new_size[1]) // 2

    return globe_frame, x_pos, y_pos

while True:
    # Check for button B press to toggle display on/off
    buttonB_is_pressed = not buttonB.value
    if buttonB_is_pressed and not buttonB_was_pressed:
        # Button B was just pressed (rising edge detection)
        display_on = not display_on
    buttonB_was_pressed = buttonB_is_pressed

    # Check for button A press to cycle pages
    buttonA_is_pressed = not buttonA.value
    if buttonA_is_pressed and not buttonA_was_pressed:
        # Button A was just pressed - cycle to next page
        if display_mode == "pihole":
            display_mode = "system"
        elif display_mode == "system":
            display_mode = "globe"
        else:  # globe
            display_mode = "pihole"

        # Reset globe animation frame when entering globe page
        if display_mode == "globe":
            globe_frame = 0
            globe_last_update = time.time()

    buttonA_was_pressed = buttonA_is_pressed

    # Check for both buttons held together for reboot
    both_buttons_pressed = buttonA_is_pressed and buttonB_is_pressed
    if both_buttons_pressed:
        if both_buttons_hold_start is None:
            # Just started holding both buttons
            both_buttons_hold_start = time.time()
        else:
            # Check how long they've been held
            hold_duration = time.time() - both_buttons_hold_start
            if hold_duration >= REBOOT_HOLD_DURATION:
                # Display reboot warning
                draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=COLOR_WARN)
                reboot_msg = "REBOOTING..."
                text_w = draw.textbbox((0, 0), reboot_msg, font=font)[2]
                text_x = (CANVAS_WIDTH - text_w) // 2
                text_y = CANVAS_HEIGHT // 2
                draw.text((text_x, text_y), reboot_msg, font=font, fill=(255, 255, 255))
                disp.image(image)
                time.sleep(0.5)

                # Execute reboot
                try:
                    subprocess.run(['sudo', 'reboot'], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Reboot failed: {e}")
                except Exception as e:
                    print(f"Reboot error: {e}")
    else:
        # Buttons released, reset hold timer
        both_buttons_hold_start = None

    # If display is off, just show blank screen
    if not display_on:
        draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=(0, 0, 0))
        disp.image(image)
        time.sleep(.1)
        continue

    # Display appropriate page based on mode
    try:
        if display_mode == "pihole":
            # Gather Pi-hole stats
            cmd = "hostname -I | cut -d' ' -f1"
            IP = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
            cmd = (
                "cat /sys/class/thermal/thermal_zone0/temp | "
                "awk '{printf \"%.1f°C\", $(NF-0) / 1000}'"
            )
            Temp = subprocess.check_output(cmd, shell=True).decode("utf-8")

            # Pi Hole data
            try:
                r = requests.get(API_URL, timeout=5)
                r.raise_for_status()
                data = r.json()
                ADSBLOCKED = data["queries"]["blocked"]
                CLIENTS = data["clients"]["total"]
            except (KeyError, requests.RequestException, json.JSONDecodeError):
                ADSBLOCKED = "N/A"
                CLIENTS = "N/A"

            # Draw static Pi-hole stats
            draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=COLOR_BG)
            draw_static_display(draw, font, IP, ADSBLOCKED, CLIENTS, Temp)
            disp.image(image)

        elif display_mode == "system":
            # Gather system stats
            system_stats = get_system_stats()

            # Draw static system stats
            draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=COLOR_BG)
            draw_system_stats_display(draw, font, system_stats)
            disp.image(image)

        elif display_mode == "globe":
            # Update globe animation frame
            current_time = time.time()
            if current_time - globe_last_update >= GLOBE_FRAME_DELAY:
                globe_frame = (globe_frame + 1) % GLOBE_TOTAL_FRAMES
                globe_last_update = current_time

            # Draw spinning globe
            globe_img, x_pos, y_pos = draw_globe_animation(globe_spritesheet, globe_frame)

            # Clear background and paste globe
            draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=(0, 0, 0))
            image.paste(globe_img, (x_pos, y_pos))
            disp.image(image)

    except Exception as e:
        # Log error and continue
        print(f"Display error: {e}")

    time.sleep(.1)
