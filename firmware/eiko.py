#!/usr/bin/env python3

import os
import time
from datetime import datetime
from PIL import Image
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from rpi_ws281x import PixelStrip, Color
import ST7789

SHUTTER = 125
ENCA    = 127
ENCB    = 124
ENC2A   = 128
ENC2B   = 130
ENC2BTN = 147

TFTDC  = 132
TFTRST = 131
TFTBL  = 129
TFTCS  = 0

LEDPIN   = 144
LEDCOUNT = 24

PICS = "/home/orangepi/Pictures"
os.makedirs(PICS, exist_ok=True)

COLORS = [
    Color(255, 255, 255),
    Color(255, 0,   0),
    Color(0,   255, 0),
    Color(0,   0,   255),
    Color(0,   255, 255),
    Color(148, 0,   211),
    Color(255, 100, 0),
    Color(0,   0,   0),
]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for p in [SHUTTER, ENCA, ENCB, ENC2A, ENC2B, ENC2BTN]:
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)

strip = PixelStrip(LEDCOUNT, LEDPIN, 800000, 10, False, 128, 0)
strip.begin()

def setled(c):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, c)
    strip.show()

setled(Color(0, 0, 0))

cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": (240, 320), "format": "RGB888"}))
cap = cam.create_still_configuration(main={"size": (3280, 2464)})
cam.start()
time.sleep(1)

disp = ST7789.ST7789(height=320, width=240, rotation=90, port=0,
                     cs=TFTCS, dc=TFTDC, rst=TFTRST, backlight=TFTBL,
                     spi_speed_hz=80000000)

cidx   = 0
ledon  = False
elast  = GPIO.input(ENCA)
e2last = GPIO.input(ENC2A)

def shoot(ch):
    time.sleep(0.05)
    if GPIO.input(SHUTTER) == GPIO.LOW:
        fname = os.path.join(PICS, f"eiko_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        cam.switch_mode_and_capture_file(cap, fname)
        if ledon:
            setled(Color(255, 255, 255))
            time.sleep(0.08)
            setled(COLORS[cidx])

def toggle(ch):
    global ledon
    time.sleep(0.05)
    if GPIO.input(ENC2BTN) == GPIO.LOW:
        ledon = not ledon
        setled(COLORS[cidx] if ledon else Color(0, 0, 0))

def enc2(ch):
    global cidx, e2last
    a = GPIO.input(ENC2A)
    if a != e2last:
        cidx = (cidx + (1 if GPIO.input(ENC2B) != a else -1)) % len(COLORS)
        if ledon:
            setled(COLORS[cidx])
        e2last = a

GPIO.add_event_detect(SHUTTER, GPIO.FALLING, callback=shoot,  bouncetime=200)
GPIO.add_event_detect(ENC2BTN, GPIO.FALLING, callback=toggle, bouncetime=200)
GPIO.add_event_detect(ENC2A,   GPIO.BOTH,    callback=enc2)

try:
    while True:
        frame = cam.capture_array()
        disp.display(Image.fromarray(frame).resize((240, 320)))
        time.sleep(0.033)
except KeyboardInterrupt:
    pass
finally:
    cam.stop()
    setled(Color(0, 0, 0))
    GPIO.cleanup()