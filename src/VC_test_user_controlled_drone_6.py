import threading
from pymavlink import mavutil
import mavsdk
import time
import math

from gtts import gTTS
import speech_recognition as sr
import os
import time
import pyaudio
import collections
from collections.abc import MutableMapping
collections.MutableMapping = collections.abc.MutableMapping
from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException
from transformers import BertTokenizer, BertForTokenClassification
import torch
import re

# Connect to the drone via TCP
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5763')

# Wait for a heartbeat to confirm connection
print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Heartbeat received from system {connection.target_system}, component {connection.target_component}")

# --- Global Parameters ---
DEFAULT_ALTITUDE = 2.0  # Default altitude in meters
ALTITUDE_TOLERANCE = 0.4  # Tolerance for altitude maintenance (10%) Tolerance set to 0.4 for testing purposes

# --- Utility Functions ---

def is_armed():
    """Check if the drone is armed."""
    msg = connection.recv_match(type='SYS_STATUS', blocking=True)
    if msg:
        return bool(msg.system_status & mavutil.mavlink.MAV_STATE_ARMED)
    return False

def set_mode(mode):
    """Sets the drone's mode."""
    mode_id = connection.mode_mapping()[mode]
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )
    print(f"Mode set to {mode}...")

def check_arm_status():
    """Checks if the drone is armed."""
    status = connection.recv_match(type='HEARTBEAT', blocking=True)
    return status.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED > 0

def arm_check_required(func):
    """Decorator to ensure the drone is armed before executing the function."""
    def wrapper(*args, **kwargs):
        if not check_arm_status():
            print("Drone is not armed. Arming the drone before proceeding.")
            arm_disarm(True)  # Arm the drone if not already armed
            print("Drone armed. Proceeding with function execution.")
            time.sleep(5)  # Wait for the drone to arm before continuing
        return func(*args, **kwargs)  # Continue executing the function
    return wrapper

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

def get_current_altitude():
    """Retrieves the current altitude of the drone."""
    msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
    if msg:
        return msg.relative_alt / 1000.0  # Convert from mm to meters
    return None  # Return None if no valid message is received

# --- Command Functions ---
@arm_check_required
def takeoff(altitude):
    """Initiates drone takeoff to a specified altitude."""
    set_mode("GUIDED")
    arm_disarm(True)  # Ensure the drone is armed before takeoff
    print(f"Taking off to {altitude}m...")
    send_nav_command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, z=altitude)
    time.sleep(2)
    altitude = altitude - 0.05
    wait_for_altitude(altitude, ALTITUDE_TOLERANCE)
    print("Takeoff complete.")

@arm_check_required
def land():
    """Lands the drone and waits for completion."""
    print("Landing...")
    send_nav_command(mavutil.mavlink.MAV_CMD_NAV_LAND)
    time.sleep(2)
    altitude = 0
    wait_for_altitude(altitude, ALTITUDE_TOLERANCE)
    print("Landing complete.")

@arm_check_required
def move(x, y, altitude):
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

@arm_check_required
def set_altitude(altitude):
    """Sets the target altitude for the drone."""
    print(f"Setting altitude to {altitude}m...")
    time.sleep(3)

@arm_check_required
def spin(degrees):
    """Rotates the drone by a specified number of degrees."""
    time_needed = (degrees / 25) + 5  # degrees/degree turn per second
    set_mode("GUIDED")
    print(f"Rotating {degrees} degrees...")
    send_nav_command(mavutil.mavlink.MAV_CMD_CONDITION_YAW, param1=degrees, param2=25, param3=1, param4=1)
    time.sleep(time_needed)

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

@arm_check_required
def fly_to(x, y):
    set_mode("GUIDED")
    """Moves the drone to a specified X, Y position while maintaining its current altitude."""
    current_alt = get_current_altitude()
    if current_alt is None:
        print("Error: Unable to retrieve current altitude.")
        return

    print(f"Flying to X:{x}, Y:{y} while maintaining altitude at {current_alt}m")
    connection.mav.set_position_target_local_ned_send(
        0,
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        int(0b010111111000),  # Position only
        x, y, -current_alt,  # Maintain altitude
        0, 0, 0,  # No velocity
        0, 0, 0,  # No acceleration
        0, 0
    )
    time.sleep(5)  # Allow time for movement

@arm_check_required
def go_up(delta_altitude):
    """Increases the drone's altitude by the specified amount."""
    current_alt = get_current_altitude()
    if current_alt is None:
        print("Error: Unable to retrieve current altitude.")
        return

    target_altitude = current_alt + delta_altitude
    print(f"Going up by {delta_altitude}m to {target_altitude}m")
    connection.mav.set_position_target_local_ned_send(
        0,
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        int(0b010111111000),  # Position only
        0, 0, -target_altitude,  # Maintain X, Y position, update Z (altitude)
        0, 0, 0,  # No velocity
        0, 0, 0,  # No acceleration
        0, 0
    )
    time.sleep(3)  # Allow time for altitude change

@arm_check_required
def go_down(delta_altitude):
    """Decreases the drone's altitude by the specified amount."""
    current_alt = get_current_altitude()
    if current_alt is None:
        print("Error: Unable to retrieve current altitude.")
        return

    target_altitude = current_alt - delta_altitude
    print(f"Going down by {delta_altitude}m to {target_altitude}m")
    connection.mav.set_position_target_local_ned_send(
        0,
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        int(0b010111111000),  # Position only
        0, 0, -target_altitude,  # Maintain X, Y position, update Z (altitude)
        0, 0, 0,  # No velocity
        0, 0, 0,  # No acceleration
        0, 0
    )
    time.sleep(3)  # Allow time for altitude change

# --- Command Processing ---
def segment_sentence(sentence):
    """
    Segments the sentence into drone actions based on recognized patterns.
    """
    tokens = sentence.lower().split()
    processed_tokens = []
    i = 0
    
    while i < len(tokens):
        if i < len(tokens) - 1:
            if tokens[i] == "take" and tokens[i+1] == "off":
                processed_tokens.append("take_off")
                i += 2
                continue
            elif tokens[i] == "fly" and tokens[i+1] == "to":
                processed_tokens.append("fly_to")
                i += 2
                continue
            elif tokens[i] == "go" and tokens[i+1] == "up":
                processed_tokens.append("go_up")
                i += 2
                continue
            elif tokens[i] in ["spin", "rotate"]:
                processed_tokens.append("spin")
                i += 1
                continue
            elif tokens[i].isdigit():
                processed_tokens.append(tokens[i])
                i += 1
                continue
        
        # Handle single word commands or others
        if tokens[i] not in ["and", ",", ".", "by", "to"]:
            processed_tokens.append(tokens[i])
        i += 1
    
    return processed_tokens

def VC_translator(command_list):
    """
    Translates a list of segmented commands into drone control function calls.
    """
    if not command_list:
        print("No command received.")
        return

    i = 0
    while i < len(command_list):
        command = command_list[i]
        
        # Takeoff Command
        if command == "take_off":
            takeoff(DEFAULT_ALTITUDE)
        
        # Fly To Command (X, Y coordinates)
        elif command == "fly_to" and i + 2 < len(command_list):
            try:
                x, y = float(command_list[i + 1]), float(command_list[i + 2])
                fly_to(x, y)
                i += 2
            except ValueError:
                print(f"Invalid coordinates for fly_to: {command_list[i+1:i+3]}")

        # Go Up Command
        elif command == "go_up" and i + 1 < len(command_list):
            try:
                go_up(float(command_list[i + 1]))
                i += 1
            except ValueError:
                print(f"Invalid altitude for go_up: {command_list[i+1]}")

        # Go Down Command
        elif command == "go_down" and i + 1 < len(command_list):
            try:
                go_down(float(command_list[i + 1]))
                i += 1
            except ValueError:
                print(f"Invalid altitude for go_down: {command_list[i+1]}")

        # Spin Command (degrees)
        elif command == "spin" and i + 1 < len(command_list):
            try:
                spin(float(command_list[i + 1]))
                i += 1
            except ValueError:
                print(f"Invalid angle for spin: {command_list[i+1]}")

        # Move Command (X, Y, Z altitude)
        elif command == "move" and i + 3 < len(command_list):
            try:
                x, y, alt = float(command_list[i + 1]), float(command_list[i + 2]), float(command_list[i + 3])
                move(x, y, alt)
                i += 3
            except ValueError:
                print(f"Invalid move parameters: {command_list[i+1:i+4]}")

        # Home Command (Return to home position)
        elif command == "home":
            move(0, 0, DEFAULT_ALTITUDE)

        # Land Command
        elif command == "land":
            land()
        
        # Exit Command
        elif command == "exit":
            land()
            arm_disarm(False)
            print("Exiting...")
            break

        i += 1

# Main Loop
def main():
    print("Ready for voice commands. Please speak clearly.")
    while True:
        sentence = input("Command: ")
        segmented = segment_sentence(sentence)
        VC_translator(segmented)
        time.sleep(1)

if __name__ == "__main__":
    main()
