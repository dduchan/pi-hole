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

buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input()

buttonB = digitalio.DigitalInOut(board.D24)
buttonB.switch_to_input()

# Track display state and button state for toggle detection
display_on = True
buttonB_was_pressed = False
buttonA_was_pressed = False

# Animation state
animation_active = False
animation_frame = 0
animation_complete = False

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

def draw_animated_display(draw, font, frame, ip, ads_blocked, clients, cpu_temp):
    """Draw the animated display with growing text"""
    # Background
    draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=COLOR_BG)

    # Phase 1: Data growing animation (frames 0-20)
    if frame < 20:
        # Calculate scale from 0.3 to 1.0
        progress = frame / 20.0
        scale = 0.3 + (progress * 0.7)
        draw_static_display_scaled(draw, font, ip, ads_blocked, clients, cpu_temp, scale)

    # Phase 2: Show static display at full size, still centered
    else:
        draw_static_display_scaled(draw, font, ip, ads_blocked, clients, cpu_temp, 1.0)

def draw_static_display_scaled(draw, font, ip, ads_blocked, clients, cpu_temp, scale):
    """Draw the static data display with scaling animation"""
    # Temperature color
    try:
        temp_val = float(cpu_temp.replace('°C', ''))
        temp_color = COLOR_WARN if temp_val > 60 else COLOR_ACCENT
    except:
        temp_color = COLOR_ACCENT

    # Calculate center position
    center_x = CANVAS_WIDTH // 2
    center_y = CANVAS_HEIGHT // 2

    # Scale font size
    scaled_font_size = int(16 * scale)
    scaled_font_small = int(12 * scale)

    try:
        scaled_font = ImageFont.truetype(FONT_PATH, max(scaled_font_size, 8))
        scaled_font_header = ImageFont.truetype(FONT_PATH, max(scaled_font_small, 6))
    except:
        scaled_font = font
        scaled_font_header = font_small

    # Calculate positions based on scale
    y_start = int(28 * scale) + int(center_y * (1 - scale))
    line_height = int(28 * scale)
    x_offset = int(8 * scale) + int(center_x * (1 - scale))

    # Header - always centered
    header_text = "SYSTEM MONITOR"
    header_width = draw.textbbox((0, 0), header_text, font=scaled_font_header)[2]
    header_x = center_x - header_width // 2
    header_y = int(4 * scale) + int(center_y * (1 - scale) * 0.5)
    draw.text((header_x, header_y), header_text, font=scaled_font_header, fill=COLOR_ACCENT)

    # Draw data rows - always centered
    data_items = [
        ("IP ADDRESS", ip, COLOR_ACCENT),
        ("ADS BLOCKED", str(ads_blocked), COLOR_ACCENT),
        ("CLIENTS", str(clients), COLOR_ACCENT),
        ("CPU TEMP", cpu_temp, temp_color)
    ]

    for i, (label, value, color) in enumerate(data_items):
        y_pos = y_start + line_height * i
        text = f"{label}: {value}"
        text_width = draw.textbbox((0, 0), text, font=scaled_font)[2]
        text_x = center_x - text_width // 2
        draw.text((text_x, y_pos), text, font=scaled_font, fill=COLOR_TEXT)

    # Border accents at full scale only
    if scale >= 0.9:
        draw_border_accent(draw)
        # Center the header divider line
        draw.line([(center_x - 100, int(22 * scale) + int(center_y * (1 - scale) * 0.5)),
                   (center_x + 100, int(22 * scale) + int(center_y * (1 - scale) * 0.5))],
                  fill=COLOR_ACCENT, width=1)

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

while True:
    # Check for button B press to toggle display on/off
    buttonB_is_pressed = not buttonB.value
    if buttonB_is_pressed and not buttonB_was_pressed:
        # Button B was just pressed (rising edge detection)
        display_on = not display_on
    buttonB_was_pressed = buttonB_is_pressed

    # Check for button A press to start animation
    buttonA_is_pressed = not buttonA.value
    if buttonA_is_pressed and not buttonA_was_pressed:
        # Button A was just pressed - start animation
        animation_active = True
        animation_frame = 0
        animation_complete = False
    buttonA_was_pressed = buttonA_is_pressed

    # If display is off, just show blank screen
    if not display_on:
        draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=(0, 0, 0))
        disp.image(image)
        time.sleep(.1)
        continue

    # Gather system stats
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

    # Handle animation
    try:
        if animation_active:
            draw_animated_display(draw, font, animation_frame, IP, ADSBLOCKED, CLIENTS, Temp)
            animation_frame += 1

            # Animation completes at frame 20
            if animation_frame >= 20:
                animation_active = False
                animation_complete = True
        else:
            # Static display when animation is complete or not started
            if animation_complete:
                # Show final static display
                draw_animated_display(draw, font, 20, IP, ADSBLOCKED, CLIENTS, Temp)
            else:
                # Show a standby screen before first animation
                draw.rectangle((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT), outline=0, fill=COLOR_BG)

                msg = "PRESS BTN A"
                msg2 = "TO INITIALIZE"
                text_w = draw.textbbox((0, 0), msg, font=font)[2]
                text_w2 = draw.textbbox((0, 0), msg2, font=font)[2]
                text_h = draw.textbbox((0, 0), msg, font=font)[3]
                text_h2 = draw.textbbox((0, 0), msg2, font=font)[3]

                # Calculate text position
                text_x = (CANVAS_WIDTH - text_w) // 2
                text_y = CANVAS_HEIGHT // 2 - 15
                text2_y = CANVAS_HEIGHT // 2 + 10

                # Draw corner brackets around the text
                bracket_len = 30
                padding = 15

                # Top-left bracket
                top_left_x = text_x - padding
                top_left_y = text_y - padding
                draw.line([(top_left_x, top_left_y), (top_left_x, top_left_y + bracket_len)], fill=COLOR_ACCENT, width=2)
                draw.line([(top_left_x, top_left_y), (top_left_x + bracket_len, top_left_y)], fill=COLOR_ACCENT, width=2)

                # Bottom-right bracket
                bottom_right_x = text_x + max(text_w, text_w2) + padding
                bottom_right_y = text2_y + text_h2 + padding
                draw.line([(bottom_right_x, bottom_right_y), (bottom_right_x, bottom_right_y - bracket_len)], fill=COLOR_ACCENT, width=2)
                draw.line([(bottom_right_x, bottom_right_y), (bottom_right_x - bracket_len, bottom_right_y)], fill=COLOR_ACCENT, width=2)

                # Blinking text effect
                if int(time.time() * 2) % 2 == 0:
                    draw.text((text_x, text_y), msg, font=font, fill=COLOR_ACCENT)
                    draw.text(((CANVAS_WIDTH - text_w2) // 2, text2_y), msg2, font=font, fill=COLOR_TEXT)

        # Display image
        disp.image(image)
    except Exception as e:
        # Log error and continue
        print(f"Display error: {e}")

    time.sleep(.1)
