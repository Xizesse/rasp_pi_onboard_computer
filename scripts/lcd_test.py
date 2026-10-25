#!/usr/bin/env python3
"""1602A LCD test: loops 1 2 3 4 on line 1, an update counter on line 2.

Wiring (BCM numbers): RS=GPIO26, E=GPIO19, D4..D7=GPIO13,16,20,21, RW=GND.
Run in the venv: pip install RPLCD rpi-lgpio
"""
from itertools import count, cycle
from time import sleep

import RPi.GPIO as GPIO
from RPLCD.gpio import CharLCD

lcd = CharLCD(
    numbering_mode=GPIO.BCM,
    cols=16,
    rows=2,
    pin_rs=26,
    pin_e=19,
    pins_data=[13, 16, 20, 21],  # D4, D5, D6, D7 (header pins 33, 36, 38, 40)
)

try:
    lcd.clear()
    for n, digit in zip(count(1), cycle("1234")):
        lcd.cursor_pos = (0, 0)
        lcd.write_string(f"Value: {digit}".ljust(16))
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"Update #{n}".ljust(16))
        print(digit, n)
        sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    lcd.clear()
    lcd.close(clear=True)
    print("done")
