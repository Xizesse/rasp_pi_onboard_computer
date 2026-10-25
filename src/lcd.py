"""LCD service: shows whatever text the monitor sends over UDP.

Listens on 127.0.0.1:15000 for UTF-8 strings. Lines split on "\n";
without "\n" the text wraps at 16 chars. Anything past 2x16 is cut.
No packet for MONITOR_TIMEOUT seconds -> shows "NO MONITOR".

Wiring (BCM): RS=GPIO26, E=GPIO19, D4..D7=GPIO13,16,20,21, RW=GND.
"""
import signal
import socket
import sys
import time

import RPi.GPIO as GPIO
from RPLCD.gpio import CharLCD

LISTEN_ADDR = ("127.0.0.1", 15000)
COLS, ROWS = 16, 2
MONITOR_TIMEOUT = 3.0  # seconds without a packet before "NO MONITOR"
NO_MONITOR_TEXT = "NO MONITOR"


def layout(text, cols=COLS, rows=ROWS):
    """Turn a string into exactly `rows` lines of `cols` chars (pure, testable)."""
    if "\n" in text:
        lines = text.split("\n")
    else:
        lines = [text[i:i + cols] for i in range(0, len(text), cols)] or [""]
    lines = [line[:cols].ljust(cols) for line in lines[:rows]]
    while len(lines) < rows:
        lines.append(" " * cols)
    return lines


def main():
    # systemd stops services with SIGTERM; turn it into a normal exit so
    # the finally block clears the display.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    lcd = CharLCD(
        numbering_mode=GPIO.BCM,
        cols=COLS,
        rows=ROWS,
        pin_rs=26,
        pin_e=19,
        pins_data=[13, 16, 20, 21],  # D4, D5, D6, D7
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(LISTEN_ADDR)
    sock.settimeout(1.0)  # wake up every second to check for staleness

    last_rx = None   # monotonic time of the last packet; None = never
    shown = None     # lines currently on the display

    def show(lines):
        nonlocal shown
        if lines == shown:
            return  # only redraw on change
        for row, line in enumerate(lines):
            lcd.cursor_pos = (row, 0)
            lcd.write_string(line)
        shown = lines

    print(f"lcd_service listening on {LISTEN_ADDR[0]}:{LISTEN_ADDR[1]}")
    try:
        lcd.clear()
        show(layout(NO_MONITOR_TEXT))
        while True:
            try:
                data, _ = sock.recvfrom(1024)
            except socket.timeout:
                data = None

            now = time.monotonic()
            if data is not None:
                last_rx = now
                text = data.decode("ascii", errors="replace")
                lines = layout(text)
                if lines != shown:
                    print(f"show: {lines[0]!r} {lines[1]!r}")
                show(lines)
            elif last_rx is not None and now - last_rx > MONITOR_TIMEOUT:
                if shown != layout(NO_MONITOR_TEXT):
                    print("monitor silent, showing NO MONITOR")
                show(layout(NO_MONITOR_TEXT))
    except KeyboardInterrupt:
        pass
    finally:
        lcd.close(clear=True)
        sock.close()
        print("lcd_service stopped")


if __name__ == "__main__":
    main()
