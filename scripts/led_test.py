#!/usr/bin/env python3
"""LED test: all three blink together, then one by one.

Wiring (each): GPIO -> resistor -> LED long leg; short leg -> GND (pin 9).
Green GPIO17 (pin 11), yellow GPIO27 (pin 13), red GPIO22 (pin 15).
"""
from time import sleep

from gpiozero import LED

leds = {"green": LED(17), "yellow": LED(27), "red": LED(22)}

try:
    print("all blinking")
    for _ in range(5):
        for led in leds.values():
            led.on()
        sleep(0.5)
        for led in leds.values():
            led.off()
        sleep(0.5)

    print("one by one")
    for name, led in leds.items():
        print(name)
        led.on()
        sleep(1)
        led.off()
finally:
    for led in leds.values():
        led.close()
    print("done")

