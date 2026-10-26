# tests/test_failsafes.py: run on the Pi with SITL + services up
# Laptop MAVProxy first: output add <pi-ip>:14552
# Then: sudo -v && .venv/bin/pytest -v tests/test_failsafes.py
import subprocess
import time

import pytest
from pymavlink import mavutil

PARAM_FILE = 'config/boat.param'
HOLD, RTL, GUIDED = 4, 11, 15


@pytest.fixture(scope='session')
def mav():
    """One MAVLink connection for the whole run, as sysid 250."""
    m = mavutil.mavlink_connection('udpin:0.0.0.0:14552', source_system=250)
    m.wait_heartbeat(timeout=10)
    return m


@pytest.fixture
def armed_boat(mav):
    """Clean start for each test: full battery, reboot (failsafes latch), GUIDED, arm."""
    mav.param_set_send('SIM_BATT_VOLTAGE', 12.6)
    time.sleep(1)
    mav.reboot_autopilot()
    time.sleep(5)
    mav.wait_heartbeat(timeout=30)
    time.sleep(20)                                   # let GPS/EKF settle
    mav.set_mode(GUIDED)
    assert wait_mode(mav, GUIDED, timeout=10), 'mode change to GUIDED failed'
    armed, texts = wait_armed(mav, timeout=30)
    assert armed, f'arming failed: {texts[-5:]}'
    yield mav
    mav.param_set_send('SIM_BATT_VOLTAGE', 12.6)

def load_parm(path):
    """Read a .parm file into {name: value}, skipping comments and blank lines."""
    params = {}
    for line in open(path):
        line = line.split('#')[0].strip()
        if line:
            name, value = line.split()[:2]
            params[name] = float(value)
    return params


def fetch_param(m, name, timeout=3):
    """Ask the autopilot for one param (PARAM_REQUEST_READ) and wait for its PARAM_VALUE."""
    m.mav.param_request_read_send(1, 1, name.encode(), -1)
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=1)
        if msg and msg.param_id == name:
            return msg.param_value
    return None


def wait_mode(m, mode, timeout, log=None):
    """True when the autopilot reports this mode. Optionally records mode/arm changes + STATUSTEXT."""
    last = None
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        msg = m.recv_match(type=['HEARTBEAT', 'STATUSTEXT'], blocking=True, timeout=1)
        if msg is None:
            continue
        if msg.get_type() == 'STATUSTEXT':
            if log is not None:
                log.append(msg.text)
            continue
        if msg.get_srcSystem() != 1 or msg.get_srcComponent() != 1:
            continue
        armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        state = (msg.custom_mode, armed)
        if log is not None and state != last:
            log.append(f'mode {msg.custom_mode} {"ARMED" if armed else "disarmed"}')
            last = state
        if msg.custom_mode == mode:
            return True
    return False

def wait_armed(m, timeout):
    """Retry arming until the HEARTBEAT shows ARMED. Collect STATUSTEXT (PreArm reasons)."""
    texts = []
    end = time.monotonic() + timeout
    next_try = 0
    while time.monotonic() < end:
        if time.monotonic() >= next_try:
            m.arducopter_arm()
            next_try = time.monotonic() + 5            # re-send every 5 s
        msg = m.recv_match(type=['HEARTBEAT', 'STATUSTEXT'], blocking=True, timeout=1)
        if msg is None:
            continue
        if msg.get_type() == 'STATUSTEXT':
            texts.append(msg.text)
        elif (msg.get_srcSystem() == 1 and msg.get_srcComponent() == 1
                and msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            return True, texts
    return False, texts

def test_params_match_known_good(mav):
    for name, expected in load_parm(PARAM_FILE).items():
        actual = fetch_param(mav, name)
        assert actual is not None, f'{name}: no reply'
        assert abs(actual - expected) < 1e-3, f'{name}: {actual} != {expected}'


def test_low_battery_triggers_rtl(armed_boat):
    armed_boat.param_set_send('SIM_BATT_VOLTAGE', 10.3)   # below LOW 10.5, above CRT 9.9
    log = []
    assert wait_mode(armed_boat, RTL, timeout=20, log=log), f'saw: {log}'

def test_companion_loss_triggers_hold(armed_boat):
    subprocess.run(['sudo', 'systemctl', 'stop', 'monitor.service'], check=True)
    try:
        assert wait_mode(armed_boat, HOLD, timeout=15)     # FS_TIMEOUT 5 + margin
    finally:
        subprocess.run(['sudo', 'systemctl', 'start', 'monitor.service'], check=True)
