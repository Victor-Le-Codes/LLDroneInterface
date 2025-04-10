import threading
from pymavlink import mavutil
import time
import math

# Connect to the drone via TCP
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5763')

# Wait for a heartbeat to confirm connection
print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Heartbeat received from system {connection.target_system}, component {connection.target_component}")

# --- Global Parameters ---
DEFAULT_ALTITUDE = 2.0  # Default altitude in meters
ALTITUDE_TOLERANCE = 0.1  # Tolerance for altitude maintenance (10%)

# --- Utility Functions ---
def set_mode(mode):
    """Sets the drone's mode."""
    mode_id = connection.mode_mapping()[mode]
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )
    print(f"Mode set to {mode}...")

def arm_disarm(arm):
    """Arms or disarms the drone."""
    print(f"Sending {'arm' if arm else 'disarm'} command...")
    connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        int(arm), 0, 0, 0, 0, 0, 0
    )

    while True:
        msg = connection.recv_match(type='COMMAND_ACK', blocking=True)
        if msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"Action confirmed: {'Armed' if arm else 'Disarmed'}")
                return
            else:
                print(f"Error: Command not accepted (result code: {msg.result})")
                return

def send_nav_command(command, param1=0, param2=0, param3=0, param4=0, x=0, y=0, z=0):
    """Sends a navigation command to the drone."""
    connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        command,
        0,
        param1, param2, param3, param4, x, y, z
    )

# --- Command Functions ---
def takeoff(altitude):
    """Initiates drone takeoff to a specified altitude."""
    set_mode("GUIDED")
    arm_disarm(True)
    print(f"Taking off to {altitude}m...")
    send_nav_command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, z=altitude)
    time.sleep(5)
    wait_for_altitude(altitude, ALTITUDE_TOLERANCE)
    print("Takeoff complete.")

def land():
    """Lands the drone."""
    print("Landing...")
    send_nav_command(mavutil.mavlink.MAV_CMD_NAV_LAND)
    time.sleep(5)

def move(x, y, altitude):
    """Moves the drone to a specified X, Y position while maintaining altitude."""
    set_mode("GUIDED")
    print(f"Moving to X:{x}, Y:{y}, Z:{altitude}")
    connection.mav.set_position_target_local_ned_send(
        0,
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        int(0b010111111000),  # Position only
        x, y, -altitude,
        0, 0, 0,  # No velocity
        0, 0, 0,  # No acceleration
        0, 0
    )
    time.sleep(5)

def set_altitude(altitude):
    """Sets the target altitude for the drone."""
    print(f"Setting altitude to {altitude}m...")
    # Implement logic to adjust altitude (e.g., using altitude hold mode or position control)
    # The specific implementation will depend on your drone's capabilities and desired behavior
    # Example: You might send a command to change the altitude setpoint in altitude hold mode
    # set_mode("ALT_HOLD") # set mode first, then send command to change target altitude
    # send_nav_command(mavutil.mavlink.MAV_CMD_DO_CHANGE_ALTITUDE, param1=altitude) #Example command
    # Time to stabilize after command
    time.sleep(3)

def rotate(degrees):
    """Rotates the drone by a specified number of degrees."""
    set_mode("GUIDED")
    print(f"Rotating {degrees} degrees...")
    send_nav_command(mavutil.mavlink.MAV_CMD_CONDITION_YAW, param1=degrees, param2=10, param3=1, param4=0)
    time.sleep(5) #Increased sleep time to allow rotation to complete

def wait_for_altitude(target_altitude, tolerance):
    """Waits until the drone reaches the target altitude within the specified tolerance."""
    start_time = time.time()
    while True:
        msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
        if msg:
            current_altitude = msg.relative_alt / 1000.0
            print(f"Current altitude: {current_altitude:.2f}m", end='\r')
            if abs(current_altitude - target_altitude) <= tolerance * target_altitude:
                print(f"Reached target altitude of {target_altitude:.2f}m")
                return
        if time.time() - start_time > 30:
            print("Timeout waiting for altitude")
            return
        time.sleep(0.1)

# --- Main Control Loop ---
def user_control():
    """Main loop for user interaction and command execution."""
    global DEFAULT_ALTITUDE
    while True:
        print("\nAvailable Commands:")
        print("T. Takeoff (altitude)")
        print("L. Land")
        print("M. Move (x, y, altitude)")
        print("R. Rotate (degrees)")
        print("H. Home")
        print("E. Exit")

        choice = input("Enter your command number: ")

        if choice == ('t' or 'T'):
            altitude = float(input(f"Enter target altitude (default: {DEFAULT_ALTITUDE}m): ") or DEFAULT_ALTITUDE)
            takeoff(altitude)
        elif choice == ('l' or 'L'):
            land()
        elif choice == ('m' or 'M'):
            x = float(input("Enter X position: "))
            y = float(input("Enter Y position: "))
            altitude = float(input(f"Enter altitude (default: {DEFAULT_ALTITUDE}m): ") or DEFAULT_ALTITUDE)
            move(x, y, altitude)
        
             
             
        elif choice == ('r' or 'R'):
            degrees = float(input("Enter rotation in degrees: "))
            rotate(degrees)

        elif choice == ('h' or 'H'):

            move(0,0,2)
            
            land()



        elif choice == ('e' or 'E'):
            land()
            arm_disarm(False)
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

# --- Start the Script ---
if __name__ == "__main__":
    user_control()
