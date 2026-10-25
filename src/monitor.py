import socket
import time
from enum import Enum

from pymavlink import mavutil

AUTOPILOT_SYSID = 1   # MAV_SYSID on the vehicle
AUTOPILOT_COMPID = 1  # MAV_COMP_ID_AUTOPILOT1
LCD_ADDR = ("127.0.0.1", 15000)


class LinkState(Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    LOST = "LOST"


class HeartbeatMonitor:
    def __init__(self, degraded_after: float, lost_after: float):
        self.degraded_after = degraded_after
        self.lost_after = lost_after
        self.last_hb = None  # never heard one yet
        self.silence = None

    def on_heartbeat(self, now: float) -> None:
        self.last_hb = now

    def update(self, now: float) -> LinkState:
        if self.last_hb is None:
            return LinkState.LOST
        self.silence = now - self.last_hb
        if self.silence > self.lost_after:
            return LinkState.LOST
        elif self.silence > self.degraded_after:
            return LinkState.DEGRADED
        else:
            return LinkState.OK


def hms(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def lcd_text(state, mode, volts, silence):
    line1 = f"{state.value} {mode or '?'}"
    v = f"{volts:.1f}V" if volts is not None else "?V"
    if silence is None:
        line2 = f"{v} --:--:--"
    elif state == LinkState.OK:
        line2 = v
    else:
        line2 = f"{v} {hms(silence)}"
    return f"{line1}\n{line2}"

def main():
    conn = mavutil.mavlink_connection('udpin:0.0.0.0:14550')
    monitor = HeartbeatMonitor(degraded_after=2, lost_after=10)
    lcd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_state = None
    last_mode = None

    mode = None        # latest values from the autopilot
    volts = None
    remaining = None

    while True:
        msg = conn.recv_match(type=['HEARTBEAT', 'SYS_STATUS'],
                              blocking=True, timeout=1)
        now = time.monotonic()

        if (msg is not None
                and msg.get_srcSystem() == AUTOPILOT_SYSID
                and msg.get_srcComponent() == AUTOPILOT_COMPID):
            mtype = msg.get_type()
            if mtype == 'HEARTBEAT':
                monitor.on_heartbeat(now)
                mode = mavutil.mode_string_v10(msg)   # custom_mode -> "MANUAL", "HOLD", ...
            elif mtype == 'SYS_STATUS':
                # 65535 / -1 mean "unknown" in MAVLink
                if msg.voltage_battery != 65535:
                    volts = msg.voltage_battery / 1000.0   # mV -> V
                remaining = msg.battery_remaining if msg.battery_remaining >= 0 else None

        state = monitor.update(now)
        if state != last_state:
            print(f"LINK {state.value}")
            last_state = state
        if mode != last_mode:
            print(f"MODE {mode}")
            last_mode = mode

        # every loop (~1 Hz): tell the LCD what to show
        text = lcd_text(state, mode, volts, monitor.silence)       
        lcd_sock.sendto(text.encode(), LCD_ADDR)


if __name__ == "__main__":
    main()
