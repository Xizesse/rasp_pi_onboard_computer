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


def main():
    conn = mavutil.mavlink_connection('udpin:0.0.0.0:14550')
    monitor = HeartbeatMonitor(degraded_after=2, lost_after=10)
    lcd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_state = None

    while True:
        msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        now = time.monotonic()

        if (msg is not None
                and msg.get_srcSystem() == AUTOPILOT_SYSID
                and msg.get_srcComponent() == AUTOPILOT_COMPID):
            monitor.on_heartbeat(now)

        state = monitor.update(now)
        if state != last_state:
            print(f"LINK {state.value}")
            last_state = state

        # every loop (~1 Hz): tell the LCD what to show
        if monitor.silence is None:
            text = f"AP: {state.value}\nno HB yet"
        else:
            text = f"AP: {state.value}\nsilent {monitor.silence:.0f}s"
        lcd_sock.sendto(text.encode(), LCD_ADDR)


if __name__ == "__main__":
    main()
