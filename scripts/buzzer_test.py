#!/usr/bin/env python3
"""Passive buzzer test: frequency sweep, then an alarm pattern.

Wiring: GPIO18 (pin 12) -> 1 kOhm -> NPN base; emitter -> GND;
buzzer + -> 5 V, buzzer - -> collector.
Run in the venv: pip install gpiozero rpi-lgpio
"""
from time import sleep

from gpiozero import PWMOutputDevice

BUZZER_PIN =  8

buzzer = PWMOutputDevice(BUZZER_PIN, frequency=2000, initial_value=0)

try:
    # 1) Sweep: listen for the loudest frequency (passive buzzers have a resonance).
    for freq in (500, 1000, 1500, 2000, 2500, 3000, 3500, 4000):
        print(f"{freq} Hz")
        buzzer.frequency = freq
        buzzer.value = 0.5  # 50% duty = square wave
        sleep(0.6)
        buzzer.value = 0
        sleep(0.2)

    # 2) Alarm pattern: 3 fast beeps, pause, repeat 3 times.
    buzzer.frequency = 2500  # change to the loudest from the sweep
    for _ in range(3):
        for _ in range(3):
            buzzer.value = 0.5
            sleep(30.5)
            buzzer.value = 0
            sleep(0.1)
        sleep(0.6)
finally:
    buzzer.off()
    buzzer.close()
    print("done")
