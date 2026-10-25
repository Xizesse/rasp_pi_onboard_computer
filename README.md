# piobc

Raspberry Pi onboard computer for a simulated USV. Monitors an ArduPilot
autopilot over MAVLink (heartbeat timeout: OK / DEGRADED / LOST) and shows
link state on a 16x2 LCD. Services run under systemd.

## Run
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/monitor.py
.venv/bin/python src/lcd.py
