from pymavlink import mavutil
from time import sleep, time

# --- Global Parameters ---
DEFAULT_ALTITUDE = 2.0  # Default altitude in meters
ALTITUDE_TOLERANCE = 0.4  # Tolerance for altitude maintenance (10%) Tolerance set to 0.4 for testing purposes

class DroneConnection:
    def __init__(self, uri="tcp:127.0.0.1:5763"):
        self.conn = mavutil.mavlink_connection(uri, autoreconnect=True)
        self._wait_for_heartbeat()

    def _wait_for_heartbeat(self):
        print("Waiting for heartbeat…")
        self.conn.wait_heartbeat()
        print(f"Heartbeat from system {self.conn.target_system}")

    # --- Utility Functions ---
    def arm(self):
        print("Arming drone…")
        self.arm_disarm(True)

    def disarm(self):
        print("Disarming drone…")
        self.arm_disarm(False)

    def is_armed(self):
        """Check if the drone is armed."""
        msg = self.conn.recv_match(type='SYS_STATUS', blocking=True)
        return bool(msg and (msg.system_status & mavutil.mavlink.MAV_STATE_ARMED))

    def set_mode(self, mode):
        """Sets the drone's mode."""
        mode_id = self.conn.mode_mapping()[mode]
        self.conn.mav.set_mode_send(
            self.conn.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
        print(f"Mode set to {mode}...")

    def check_arm_status(self):
        """Checks if the drone is armed."""
        status = self.conn.recv_match(type='HEARTBEAT', blocking=True)
        return status.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED > 0
    
    @staticmethod
    def arm_check_required(func):
        """Decorator to ensure the drone is armed before executing the function."""
        def wrapper(self, *args, **kwargs):
            if not self.check_arm_status():
                print("Drone is not armed. Arming the drone before proceeding.")
                self.arm_disarm(True)  # Arm the drone if not already armed
                print("Drone armed. Proceeding with function execution.")
                sleep(5)  # Wait for the drone to arm before continuing
            return func(self, *args, **kwargs)  # Continue executing the function
        return wrapper
    
    def arm_disarm(self, arm):
        """Arms or disarms the drone."""
        print(f"Sending {'arm' if arm else 'disarm'} command...")
        self.conn.mav.command_long_send(
            self.conn.target_system,
            self.conn.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            int(arm), 0, 0, 0, 0, 0, 0
        )

        while True:
            msg = self.conn.recv_match(type='COMMAND_ACK', blocking=True)
            if msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                    print(f"Action confirmed: {'Armed' if arm else 'Disarmed'}")
                    return
                else:
                    print(f"Error: Command not accepted (result code: {msg.result})")
                    return
                
    def send_nav_command(self, command, param1=0, param2=0, param3=0, param4=0, x=0, y=0, z=0):
        """Sends a navigation command to the drone."""
        self.conn.mav.command_long_send(
            self.conn.target_system,
            self.conn.target_component,
            command,
            0,
            param1, param2, param3, param4, x, y, z
        )

    def get_current_altitude(self):
        """Retrieves the current altitude of the drone."""
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if msg:
            return msg.relative_alt / 1000.0  # Convert from mm to meters
        return None  # Return None if no valid message is received
    
    # --- Command Functions ---
    @arm_check_required
    def takeoff(self, altitude):
        """Initiates drone takeoff to a specified altitude."""
        self.set_mode("GUIDED")
        self.arm_disarm(True)  # Ensure the drone is armed before takeoff
        print(f"Taking off to {altitude}m...")
        self.send_nav_command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, z=altitude)
        sleep(2)
        altitude = altitude - 0.05
        self.wait_for_altitude(altitude, ALTITUDE_TOLERANCE)
        print("Takeoff complete.")

    @arm_check_required
    def land(self):
        """Lands the drone and waits for completion."""
        print("Landing...")
        self.send_nav_command(mavutil.mavlink.MAV_CMD_NAV_LAND)
        sleep(2)
        altitude = 0
        self.wait_for_altitude(altitude, ALTITUDE_TOLERANCE)
        print("Landing complete.")

    @arm_check_required
    def move(self, x, y, altitude):
        self.set_mode("GUIDED")
        print(f"Moving to X:{x}, Y:{y}, Z:{altitude}")
        self.conn.mav.set_position_target_local_ned_send(
            0,
            self.conn.target_system,
            self.conn.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b010111111000),  # Position only
            x, y, -altitude,
            0, 0, 0,  # No velocity
            0, 0, 0,  # No acceleration
            0, 0
        )
        sleep(5)

    @arm_check_required
    def set_altitude(self, altitude):
        """Sets the target altitude for the drone."""
        print(f"Setting altitude to {altitude}m...")
        sleep(3)

    @arm_check_required
    def spin(self, degrees):
        """Rotates the drone by a specified number of degrees."""
        time_needed = (degrees / 25) + 5  # degrees/degree turn per second
        self.set_mode("GUIDED")
        print(f"Rotating {degrees} degrees...")
        self.send_nav_command(mavutil.mavlink.MAV_CMD_CONDITION_YAW, param1=degrees, param2=25, param3=1, param4=1)
        sleep(time_needed)

    def wait_for_altitude(self, target_altitude, tolerance):
        """Waits until the drone reaches the target altitude within the specified tolerance."""
        start_time = time()
        while True:
            msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
            if msg:
                current_altitude = msg.relative_alt / 1000.0
                print(f"Current altitude: {current_altitude:.2f}m", end='\r')
                if abs(current_altitude - target_altitude) <= tolerance * target_altitude:
                    print(f"Reached target altitude of {target_altitude:.2f}m")
                    return
            if time() - start_time > 30:
                print("Timeout waiting for altitude")
                return
            sleep(0.1)

    @arm_check_required
    def fly_to(self, x, y):
        self.set_mode("GUIDED")
        """Moves the drone to a specified X, Y position while maintaining its current altitude."""
        current_alt = self.set_current_altitude()
        if current_alt is None:
            print("Error: Unable to retrieve current altitude.")
            return

        print(f"Flying to X:{x}, Y:{y} while maintaining altitude at {current_alt}m")
        self.conn.mav.set_position_target_local_ned_send(
            0,
            self.conn.target_system,
            self.conn.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b010111111000),  # Position only
            x, y, -current_alt,  # Maintain altitude
            0, 0, 0,  # No velocity
            0, 0, 0,  # No acceleration
            0, 0
        )
        sleep(5)  # Allow time for movement

    @arm_check_required
    def go_up(self, delta_altitude):
        """Increases the drone's altitude by the specified amount."""
        current_alt = self.get_current_altitude()
        if current_alt is None:
            print("Error: Unable to retrieve current altitude.")
            return

        target_altitude = current_alt + delta_altitude
        print(f"Going up by {delta_altitude}m to {target_altitude}m")
        self.conn.mav.set_position_target_local_ned_send(
            0,
            self.conn.target_system,
            self.conn.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b010111111000),  # Position only
            0, 0, -target_altitude,  # Maintain X, Y position, update Z (altitude)
            0, 0, 0,  # No velocity
            0, 0, 0,  # No acceleration
            0, 0
        )
        sleep(3)  # Allow time for altitude change

    @arm_check_required
    def go_down(self, delta_altitude):
        """Decreases the drone's altitude by the specified amount."""
        current_alt = self.get_current_altitude()
        if current_alt is None:
            print("Error: Unable to retrieve current altitude.")
            return

        target_altitude = current_alt - delta_altitude
        print(f"Going down by {delta_altitude}m to {target_altitude}m")
        self.conn.mav.set_position_target_local_ned_send(
            0,
            self.conn.target_system,
            self.conn.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b010111111000),  # Position only
            0, 0, -target_altitude,  # Maintain X, Y position, update Z (altitude)
            0, 0, 0,  # No velocity
            0, 0, 0,  # No acceleration
            0, 0
        )
        sleep(3)  # Allow time for altitude change
