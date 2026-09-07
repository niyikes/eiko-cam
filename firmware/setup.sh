#!/bin/bash
sudo apt update
sudo apt install -y python3-pip python3-pil python3-rpi.gpio
pip3 install picamera2 rpi-ws281x st7789 pillow --break-system-packages
mkdir -p /home/orangepi/Pictures
echo "done, run: sudo python3 eiko.py"
 
