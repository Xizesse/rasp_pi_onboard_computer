from pymavlink import mavutil

conn = mavutil.mavlink_connection('udpin:0.0.0.0:14550')
conn.wait_heartbeat()
print(f"Connected to system {conn.target_system}, component {conn.target_component}")

while True:
    msg = conn.recv_match(type=['HEARTBEAT', 'GLOBAL_POSITION_INT', 'SYS_STATUS'], blocking=True)
    t = msg.get_type()

    if t == 'HEARTBEAT':
        armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        mode = mavutil.mode_string_v10(msg)
        print(f"HB    mode {mode}  {'ARMED' if armed else 'disarmed'}")

    elif t == 'GLOBAL_POSITION_INT':
        print(f"POS   {msg.lat / 1e7:.6f}, {msg.lon / 1e7:.6f}  "
              f"hdg {msg.hdg / 100:.1f}°  alt {msg.relative_alt / 1000:.2f} m")

    elif t == 'SYS_STATUS':
        print(f"BATT  {msg.voltage_battery / 1000:.2f} V  {msg.battery_remaining}%")
