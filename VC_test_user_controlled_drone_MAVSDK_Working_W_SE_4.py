import threading
from pymavlink import mavutil
import mavsdk
import time
import math

from gtts import gTTS
# import speech_recognition as sr
import os
import time
import pyaudio
import pygame
import collections
from collections.abc import MutableMapping
collections.MutableMapping = collections.abc.MutableMapping
from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException

import os
import sys
import subprocess
import contextlib

@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as fnull:
        stderr_fd = sys.stderr.fileno()
        with os.fdopen(os.dup(stderr_fd), 'w') as old_stderr:
            os.dup2(fnull.fileno(), stderr_fd)
            try:
                yield
            finally:
                os.dup2(old_stderr.fileno(), stderr_fd)

# Example usage:
with suppress_stderr():
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    mic = sr.Microphone()





"""
AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,

"""

from transformers import (
    
    BertTokenizer, 
    BertForTokenClassification
)


import torch
import re
from difflib import get_close_matches
import functools


# Changes to ensure MAVSDK compatibility

import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw
import math





WAYPOINTS = {
    "home": [0, 0, 1],
    "chair": [1, 2.5, 0.9],
    "desk": [4, 1.3, 1.3],
    "filing _cabinet": [5.5, 1, 1.2],
    "board": [4.5, -2.0, 1.4],
    "tv": [1.1, -2.9, 0.8],
    "router": [2.6, 0.3, 0.7],
    "shredder": [5.5, 1, 1.3],
    "microphone": [3.4, -1.6, 1],
    "water_dispenser": [2.5, -2.6, 1.2],
    "coffee_machine": [4.0, -2.9, 1],
    "cat": [-0.5, 2.6, 1],
    "a": [0.2, 0.2, 0.5],
    "b": [-0.2, 0.2, 0.5],
    "c": [-0.2, -0.2, 0.5],
    "d": [0.2, -0.2, 0.5]

    # Add more waypoints here
}


# Initialize pygame mixer
pygame.mixer.init()

# pygame added for sound effects:

def play_audio(file_path):
    """Function to play an audio file using pygame."""
    try:
        # Stop any previous audio playback
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()


        # Load and play the new audio file
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()


        # Wait for the playback to finish
        while pygame.mixer.music.get_busy():
            continue


        # Quit the mixer to release the file handle
        pygame.mixer.quit()
        time.sleep(0.2)  # Allow time for the system to release the file lock
        pygame.mixer.init()  # Reinitialize the mixer for the next playback
    except Exception as e:
        print(f"Error playing audio: {e}")




# --- Command Processing ---

def run_WakeWord(turnOn):
    """Function to listen for the wake word and recognize commands."""
    running = True  # Flag to control the main loop
    while turnOn and running:
        # Listen for the wake word
        print("Waiting for the wake word 'Okay Steven' or 'Hey Steven'...")
        wake_word_detected = False
       
        while not wake_word_detected:
            wake_prompt = recognize_speech()
            if wake_prompt and ("ok steven" or "ok stephen" or "hey steven" or "hey stephen") in wake_prompt.lower():
                wake_word_detected = True
                play_audio("GA_Mic_Start.mp3")
                print("Wake word 'Steven' detected! Listening for your command...")
                
            elif wake_prompt:
                print(f"You said: {wake_prompt}. Waiting for the wake word 'Steven'.")
       
        # Once the wake word is detected, listen for a command
        command = recognize_speech()
        if command is None:
            continue  # Retry if no valid speech input was detected

        # Print the recognized command
        print(f"You said: {command}")

        play_audio("GA_Voice_Command_Recognized.mp3")

        def normalize_goodbye(user_input):
            normalized = user_input.lower().replace(" ", "")  # Converts "Good bye" -> "goodbye"
            return "goodbye" if normalized in ["goodbye", "bye"] else user_input

        command = normalize_goodbye(command)

        # Check for exit condition
        if command.lower() == "goodbye":
            print("Goodbye! Exiting the program.")
            running = False  # Set the running flag to False to exit the loop
            break

        else:
            segments = segment_sentence(command)
            print("Segmented command:", segments)

            return segments

    return running  # Return the status of the running flag


def run_OneVCOnly(turnOn):

    """Function to listen for the wake word and recognize commands."""
    running = True  # Flag to control the main loop
    while turnOn and running:
        # Listen for the wake word
        # print("Waiting for the wake word 'Okay Steven' or 'Hey Steven'...")
        wake_word_detected = True
       
        while not wake_word_detected:
            play_audio("GA_Mic_Start.mp3")
            wake_prompt = recognize_speech()
            if wake_prompt and ("ok steven" or "ok stephen" or "hey steven" or "hey stephen") in wake_prompt.lower():
                wake_word_detected = True
                print("Wake word 'Steven' detected! Listening for your command...")
            elif wake_prompt:
                print(f"You said: {wake_prompt}. Waiting for the wake word 'Steven'.")
       
        # Once the wake word is detected, listen for a command
        command = recognize_speech()
        if command is None:
            continue  # Retry if no valid speech input was detected

        # Print the recognized command
        print(f"You said: {command}")

        play_audio("GA_Voice_Command_Recognized.mp3")

        def normalize_goodbye(user_input):
            normalized = user_input.lower().replace(" ", "")  # Converts "Good bye" -> "goodbye"
            return "goodbye" if normalized in ["goodbye", "bye"] else user_input

        command = normalize_goodbye(command)

        # Check for exit condition
        if command.lower() == "goodbye":
            print("Goodbye! Exiting the program.")
            running = False  # Set the running flag to False to exit the loop
            break

        else:
            segments = segment_sentence(command)
            print("Segmented command:", segments)

            return segments

    return running  # Return the status of the running flag



def recognize_speech():
    """Function to recognize speech using the microphone."""
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=30)
            query = recognizer.recognize_google(audio)
            return query
        except sr.UnknownValueError:
            play_audio("GA_No_Voice_Detected.mp3")
            print("Sorry, I couldn't understand that. Please try again.")
            return None
        except sr.RequestError as e:
            play_audio("GA_No_Voice_Detected.mp3")
            print(f"Could not request results; {e}")
            return None
        except sr.WaitTimeoutError:
            play_audio("GA_No_Voice_Detected.mp3")
            print("No speech detected. Please try again.")
            return None
        
# Initialize the speech recognizer
recognizer = sr.Recognizer()

def segment_sentence(sentence):
    """
    Segments the sentence into drone actions based on recognized patterns.
    Filters out non-relevant words (like 'to', 'by', 'and', etc.) and splits multi-digit numbers,
    except for cases like 'spin', 'rotate', 'spend', etc.
    """
    # Preprocess the sentence to split multi-digit numbers into individual digits
    sentence = re.sub(r'(\d+)', lambda x: ' '.join(list(x.group(0))), sentence)
    
    # Convert the sentence to lowercase and split into tokens
    tokens = sentence.lower().split()
    
    processed_tokens = []
    i = 0
    
    while i < len(tokens):
        # Skip irrelevant words (e.g., 'to', 'by', 'and', etc.)
        if tokens[i] in ["to", "by", "and", "in", "on", "at", "for", ",", ".", "space", "go", "the", "find"]:
            i += 1
            continue
        
        if tokens[i] == "take" and tokens[i+1] == "off":
            processed_tokens.append("takeoff")
            i += 2
            continue
        elif tokens[i] == "filing" and tokens[i+1] == "cabinet":
            processed_tokens.append("filing_cabinet")
            i += 2
            continue
        elif tokens[i] == "water" and tokens[i+1] == "dispenser":
            processed_tokens.append("water_dispenser")
            i += 2
            continue
        elif tokens[i] == "coffee" and tokens[i+1] == "machine":
            processed_tokens.append("coffee_machine")
            i += 2
            continue
        elif tokens[i] in ["spin", "rotate", "spend"]:
            # Don't split numbers after 'spin', 'rotate', 'spend'
            processed_tokens.append("rotate")
            i += 1  # Skip the number part
            continue
        elif tokens[i] in ["move", "fly"]:  # Handle commands like move, fly
            processed_tokens.append("move")  # Treat both 'move' and 'fly' as 'move'
            i += 1  # Move to the next token
            # If the next token is a number, treat it as a whole
            if i < len(tokens) and tokens[i].isdigit():
                processed_tokens.append(tokens[i])
                i += 1  # Skip the number part
            continue
        # elif tokens[i].isdigit():  # Handle other numbers as they are
        #     processed_tokens.append(tokens[i])
        #     i += 1
        #     continue

        # Negative Number Processing from -20 to 0

        if tokens[i] == "zero":
            processed_tokens.append("0")
            continue

        elif tokens[i] == "negative" and tokens[i+1] == "one":
            processed_tokens.append("-1")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i] == "negative" and tokens[i+1] == "two":
            processed_tokens.append("-2")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "three":
            processed_tokens.append("-3")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "four":
            processed_tokens.append("-4")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "five":
            processed_tokens.append("-5")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "six":
            processed_tokens.append("-6")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "seven":
            processed_tokens.append("-7")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "eight":
            processed_tokens.append("-8")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "nine":
            processed_tokens.append("-9")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "ten":
            processed_tokens.append("-10")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "eleven":
            processed_tokens.append("-11")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "twelve":
            processed_tokens.append("-12")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "thirteen":
            processed_tokens.append("-13")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "fourteen":
            processed_tokens.append("-14")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "fifteen":
            processed_tokens.append("-15")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "sixteen":
            processed_tokens.append("-16")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "seventeen":
            processed_tokens.append("-17")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "eighteen":
            processed_tokens.append("-18")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "nineteen":
            processed_tokens.append("-19")
            i += 2
            continue
        elif tokens[i] == "negative" and tokens[i+1] == "twenty":
            processed_tokens.append("-20")
            i += 2
            continue



        # Process positive numbers from 1 to 20

        elif tokens[i] == "one":
            processed_tokens.append("1")
            i += 1
            continue
        elif tokens[i] == "two":
            processed_tokens.append("2")
            i += 1
            continue
        elif tokens[i] == "three":
            processed_tokens.append("3")
            i += 1
            continue
        elif tokens[i] == "four":
            processed_tokens.append("4")
            i += 1
            continue
        elif tokens[i] == "five":
            processed_tokens.append("5")
            i += 1
            continue
        elif tokens[i] == "six":
            processed_tokens.append("6")
            i += 1
            continue
        elif tokens[i] == "seven":
            processed_tokens.append("7")
            i += 1
            continue
        elif tokens[i] == "eight":
            processed_tokens.append("8")
            i += 1
            continue
        elif tokens[i] == "nine":
            processed_tokens.append("9")
            i += 1
            continue
        elif tokens[i] == "ten":
            processed_tokens.append("10")
            i += 1
            continue
        elif tokens[i] == "eleven":
            processed_tokens.append("11")
            i += 1
            continue
        elif tokens[i] == "twelve":
            processed_tokens.append("12")
            i += 1
            continue
        elif tokens[i] == "thirteen":
            processed_tokens.append("13")
            i += 1
            continue
        elif tokens[i] == "fourteen":
            processed_tokens.append("14")
            i += 1
            continue
        elif tokens[i] == "fifteen":
            processed_tokens.append("15")
            i += 1
            continue
        elif tokens[i] == "sixteen":
            processed_tokens.append("16")
            i += 1
            continue
        elif tokens[i] == "seventeen":
            processed_tokens.append("17")
            i += 1
            continue
        elif tokens[i] == "eighteen":
            processed_tokens.append("18")
            i += 1
            continue
        elif tokens[i] == "nineteen":
            processed_tokens.append("19")
            i += 1
            continue
        elif tokens[i] == "twenty":
            processed_tokens.append("20")
            i += 1
            continue


        elif re.match(r'^[a-z]+$', tokens[i]):  # Only word tokens (like "move")
            processed_tokens.append(tokens[i])
            i += 1
            continue
            
        
        # Default to just appending the token if it's not caught by any condition
        else:
            processed_tokens.append(tokens[i])
            i += 1
            continue

        
    
    return processed_tokens

# async def VC_translator(drone, command_list):
#     """
#     Translates a list of segmented commands into drone control function calls.
#     """
#     if not command_list:
#         print("No command received.")
#         return
    
#     print("command list:", command_list)
#     print()

#     i = 0
#     while i < len(command_list):
#         command = [i]
        
#         # Takeoff Command
#         if command == "takeoff":
#             await DroneController.takeoff(drone, altitude=DEFAULT_ALTITUDE)

#         # Spin Command (degrees)
#         elif command == "spin" and i + 1 < len(command_list):
#             try:
#                 await DroneController.rotate(drone, (float(command_list[i + 1])))
#                 i += 1
#             except ValueError:
#                 print(f"Invalid angle for spin: {command_list[i+1]}")

#         # Move Command (X, Y, Z altitude)
#         elif command == "move" and i + 3 < len(command_list):
#             try:
#                 x, y, alt = float(command_list[i + 1]), float(command_list[i + 2]), float(command_list[i + 3])
#                 await DroneController.move_to_position(drone, x, y, alt)
#                 i += 3
#             except ValueError:
#                 print(f"Invalid move parameters: {command_list[i+1:i+4]}")

#         # Land Command
#         elif command == "land":
#             await DroneController.land(drone)

#         # Other commands as needed...

#         i += 1





# Drone class provided by Richie Ryu Suganda  

class DroneController:
    """A class to control a drone via MAVSDK connection."""
    
    def __init__(self, connection_string="udp://0.0.0.0:14540"): # 14540 for sim 14550 for real drone
        """
        Initialize the drone controller with a MAVSDK connection.
        
        Args:
            connection_string: MAVSDK connection string (e.g., 'udp://0.0.0.0:14540')
        """
        # Connection parameters
        self.drone = System()
        self.connection_string = connection_string
        self.DEFAULT_ALTITUDE = 0.5
        self.ALTITUDE_TOLERANCE = 0.1
        self.last_position = None
        self.last_global_position = None
        self._armed = False
        self._position_updater = None
        self._global_position_updater = None
        self._armed_updater = None

    async def connect(self):
        """Establish connection to the drone and wait for heartbeat."""
        print("Connecting to drone...")
        await self.drone.connect(system_address=self.connection_string)
        
        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("Drone connected!")
                break
        
        print("Waiting for drone to have a global position estimate...")
        timeout = 1  # Maximum wait time in seconds
        start_time = asyncio.get_event_loop().time()

        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok:
                print("Global position estimate OK")
                break
            if asyncio.get_event_loop().time() - start_time > timeout:
                print("Timed out waiting for global position estimate. Proceeding anyway.")
                break
        
        # Start background updaters
        self._position_updater = asyncio.create_task(self._update_position())
        self._global_position_updater = asyncio.create_task(self._update_global_position())
        self._armed_updater = asyncio.create_task(self._update_armed_status())
        await asyncio.sleep(1)  # Let updates initialize
    
    async def _update_position(self):
        """Background task to update position"""
        async for position in self.drone.telemetry.position_velocity_ned():
            self.last_position = (
                position.position.north_m,
                position.position.east_m,
                position.position.down_m
            )

    async def _update_global_position(self):
        """Background task to update global position"""
        async for position in self.drone.telemetry.position():
            self.last_global_position = (
                position.latitude_deg,
                position.longitude_deg,
                position.absolute_altitude_m
            )

    async def _update_armed_status(self):
        """Background task to update armed status"""
        async for armed in self.drone.telemetry.armed():
            self._armed = armed

    async def is_armed(self):
        """Check if drone is armed"""
        return self._armed

    async def get_current_altitude(self):
        """Get current altitude (positive up)"""
        pos = await self.get_position()
        return -pos[2] if pos else None

    # --- Core Utility Methods ---
    
    async def check_ekf_status(self):
        """Check if EKF is in a good state"""
        async for status in self.drone.telemetry.status_text():
            if "EKF" in status.text:
                print(f"EKF Status: {status.text}")
                if "EKF OK" in status.text or "EKF2 OK" in status.text:
                    return True
        return False

    async def pre_arm_checks(self):
        """Perform necessary pre-arm checks"""
        print("Running pre-arm checks...")
        
        async for health in self.drone.telemetry.health():
            if not health.is_armable:
                print(f"Pre-arm check failed: {health}")
                await asyncio.sleep(1)
                continue
            print("Pre-arm checks passed")
            return True
        return False

    async def set_mode(self, mode):
        """Set the drone's flight mode."""
        try:
            await self.drone.action.set_mode(mode)
            print(f"Mode set to {mode}")
        except Exception as e:
            print(f"Error setting mode: {e}")
    
    async def arm_disarm(self, arm=True):
        """Arm or disarm the drone with better error handling."""
        action = "Arming" if arm else "Disarming"
        print(f"{action} drone...")
        
        try:
            if arm:
                # Check if already armed
                if await self.is_armed():
                    print("Already armed")
                    return True
                    
                # Additional checks
                async for health in self.drone.telemetry.health():
                    if not health.is_armable:
                        print(f"Cannot arm: Health status - {health}")
                        return False
                    break
                    
            # Perform arm/disarm
            if arm:
                await self.drone.action.arm()
            else:
                await self.drone.action.disarm()
                
            print(f"Success: {'Armed' if arm else 'Disarmed'}")
            return True
        except Exception as e:
            print(f"Error {'arming' if arm else 'disarming'}: {str(e)}")
            return False
        
    async def get_position(self):
        """
        Get the current local position in NED (North-East-Down) coordinates.
        Returns: (x, y, z) in meters or None if unavailable
        """
        try:
            position_velocity = await self.drone.telemetry.position_velocity_ned().__anext__()
            self.last_position = (
                position_velocity.position.north_m,
                position_velocity.position.east_m,
                position_velocity.position.down_m
            )
            return self.last_position
        except Exception as e:
            print(f"Error getting position: {e}")
            return None

    async def get_global_position(self):
        """
        Get the current global position in GPS coordinates.
        Returns: (lat, lon, alt) or None if unavailable
                lat/lon in degrees, alt in meters
        """
        try:
            position = await self.drone.telemetry.position().__anext__()
            self.last_global_position = (
                position.latitude_deg,
                position.longitude_deg,
                position.absolute_altitude_m
            )
            return self.last_global_position
        except Exception as e:
            print(f"Error getting global position: {e}")
            return None
    
    async def engage_hold_mode(self):
        """Switch to Hold mode and verify engagement"""
        try:
            print("Attempting to switch to HOLD mode")
            await self.set_mode("HOLD")
            
            # Verify mode change
            async for flight_mode in self.drone.telemetry.flight_mode():
                if flight_mode == "HOLD":
                    print("Successfully engaged HOLD mode")
                    break
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Failed to engage HOLD mode: {e}")
            raise

    async def print_position(self):
        """Print both local and global position information."""
        local_pos = await self.get_position()
        global_pos = await self.get_global_position()
        
        print("\n=== Current Position ===")
        if local_pos:
            x, y, z = local_pos
            print(f"Local NED Position: X:{x:.2f}m, Y:{y:.2f}m, Z:{z:.2f}m (Down)")
        else:
            print("Local position unavailable")
            
        if global_pos:
            lat, lon, alt = global_pos
            print(f"Global Position: Lat:{lat:.6f}°, Lon:{lon:.6f}°, Alt:{alt:.2f}m MSL")
        else:
            print("Global position unavailable")
        print("=======================")
    

    # --- Flight Movement Methods ---
    
    async def takeoff(self, altitude=None):
        """Execute takeoff to specified altitude"""
        print("Starting takeoff sequence...")
        
        altitude = float(altitude) if altitude is not None else self.DEFAULT_ALTITUDE
        # altitude = 1.0
        if not await self.is_armed():
            print("Running pre-arm checks...")
            if not await self.pre_arm_checks():
                raise RuntimeError("Pre-arm checks failed")
                
            print("Arming drone...")
            await self.arm_disarm(True)
            await asyncio.sleep(4)  # Give time for arming to complete
        
        print(f"Setting takeoff altitude to {altitude}m...")
        await self.drone.action.set_takeoff_altitude(altitude)
        
        print("Initiating takeoff...")
        await self.drone.action.takeoff()

        asyncio.sleep(20)
        
        print("Waiting to reach target altitude...")
        await self.wait_for_altitude(altitude)
        print("Takeoff complete")

    async def land(self):
        """Execute landing sequence."""
        print("Landing...")
        await self.drone.action.land()
        await self.wait_for_altitude(0)
        print("Landing complete")
        await self.arm_disarm(False)
    
    async def calculate_target_yaw(self, current_pos, target_pos):
        """Calculate yaw angle (in degrees) to face the target position"""
        if current_pos is None or target_pos is None:
            return 0.0  # Default to 0 if position data is unavailable
        
        dx = target_pos[0] - current_pos[0]  # North (X) difference
        dy = target_pos[1] - current_pos[1]  # East (Y) difference
        
        # Calculate yaw in radians, then convert to degrees
        yaw_rad = math.atan2(dy, dx)
        yaw_deg = math.degrees(yaw_rad)
        
        # Normalize to 0-360 range
        yaw_deg = yaw_deg % 360
        return yaw_deg

    async def move_to_position(self, x, y, z=None, timeout=20):
        """Improved movement with position verification"""
        current_alt = await self.get_current_altitude()
        if current_alt is None:
            raise RuntimeError("Unable to determine current altitude")
        
        current_pos = await self.get_position()
        if current_pos is None:
            raise RuntimeError("Unable to determine current position")

        target_z = -(z if z is not None else current_alt)
        print(f"Moving to X:{x:.2f}, Y:{y:.2f}, Z:{-target_z:.2f}")
        target_yaw = await self.calculate_target_yaw(current_pos, (x, y, target_z))

        try:
            # await self.set_mode("OFFBOARD")
            await asyncio.sleep(0.5)
            # Start offboard mode
            await self.drone.offboard.set_position_ned(PositionNedYaw(x, y, target_z, target_yaw))
            await self.drone.offboard.start()
            
            # Monitor position with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                pos = await self.get_position()
                if pos:
                    error = ((pos[0]-x)**2 + (pos[1]-y)**2 + (pos[2]-target_z)**2)**0.5
                    print(f"Position error: {error:.2f}m", end='\r')
                    if error < 0.3:  # Close enough to target
                        print("\nReached target position")
                        break
                await asyncio.sleep(0.2)

            # await self.engage_hold_mode()

        except Exception as e:
            print(f"Movement error: {e}")
            raise
        finally:
            try:
                await self.drone.offboard.stop()
            except:
                pass
    
    async def move_to_position3(self, x, y, z=None, timeout=20):
        """Improved movement with position verification"""
        current_alt = await self.get_current_altitude()
        if current_alt is None:
            raise RuntimeError("Unable to determine current altitude")
        
        current_pos = await self.get_position()
        if current_pos is None:
            raise RuntimeError("Unable to determine current position")
        x_pos, y_pos, z_pos = current_pos

        target_z = -(z if z is not None else current_alt)
        print(f"Moving to X:{x:.2f}, Y:{y:.2f}, Z:{-target_z:.2f}")
        target_yaw = await self.calculate_target_yaw(current_pos, (x, y, target_z))

        try:
            # await self.set_mode("OFFBOARD")
            await asyncio.sleep(0.5)
            start_time = time.time()
            # Face the position
            while time.time() - start_time < timeout:
                # Start offboard mode
                await self.drone.offboard.set_position_ned(PositionNedYaw(x_pos, y_pos, z_pos, target_yaw))
                await self.drone.offboard.start()
                
                # Monitor position with timeout
                start_time = time.time()
                
                current_yaw = await self.get_current_yaw()
                if current_yaw:
                    error_yaw = (target_yaw - current_yaw)**2
                    print(f"Yaw error: {error_yaw:.2f}m", end='\r')
                    if error < 0.2:  # Close enough to target
                        print("\nReached target position")
                        break
                await asyncio.sleep(0.2)
            # Go into position
            while time.time() - start_time < timeout:
                # Start offboard mode
                await self.drone.offboard.set_position_ned(PositionNedYaw(x, y, target_z, target_yaw))
                await self.drone.offboard.start()
                
                # Monitor position with timeout
                start_time = time.time()
                
                pos = await self.get_position()
                if pos:
                    error = ((pos[0]-x)**2 + (pos[1]-y)**2 + (pos[2]-target_z)**2)**0.5
                    print(f"Position error: {error:.2f}m", end='\r')
                    if error < 0.3:  # Close enough to target
                        print("\nReached target position")
                        break
                await asyncio.sleep(0.2)

            # await self.engage_hold_mode()

        except Exception as e:
            print(f"Movement error: {e}")
            raise
        finally:
            try:
                await self.drone.offboard.stop()
            except:
                pass
    

    async def move_to_position2(self, x, y, z=None, timeout=20, update_rate=10):
        """Improved movement with position verification"""
        current_alt = await self.get_current_altitude()
        if current_alt is None:
            raise RuntimeError("Unable to determine current altitude")
        
        current_pos = await self.get_position()
        if current_pos is None:
            raise RuntimeError("Unable to determine current position")

        target_z = -(z if z is not None else current_alt)
        print(f"Moving to X:{x:.2f}, Y:{y:.2f}, Z:{-target_z:.2f}")
        target_yaw = await self.calculate_target_yaw(current_pos, (x, y, target_z))

        try:
            await asyncio.sleep(0.5)
            # Start offboard mode
            await self.drone.offboard.set_position_ned(PositionNedYaw(x, y, target_z, target_yaw))
            await self.drone.offboard.start()
            
            # Monitor position with timeout
            start_time = time.time()
            last_update = time.time()
            update_interval = 1.0 / update_rate
            while time.time() - start_time < timeout:
                current_time = time.time()
                if current_time - last_update < update_interval:
                    await asyncio.sleep(0.01)
                    continue
                    
                last_update = current_time
                
                # Get current position
                current_pos = await self.get_position()
                if current_pos is None:
                    continue
                    
                # Calculate progress (0-1)
                elapsed = current_time - start_time
                progress = min(elapsed / timeout, 1.0)
                
                # Calculate intermediate target (gradual approach)
                cmd_x = current_pos[0] + (x - current_pos[0]) * 0.1  # 10% of remaining distance
                cmd_y = current_pos[1] + (y - current_pos[1]) * 0.1
                cmd_z = current_pos[2] + (target_z - current_pos[2]) * 0.1
                
                # Adjust yaw to always face the final target
                current_yaw = await self.get_current_yaw()
                yaw_diff = (target_yaw - current_yaw + 180) % 360 - 180  # Shortest angle
                cmd_yaw = current_yaw + 0.3 * yaw_diff  # Smooth yaw transition
                
                # Send position command
                await self.drone.offboard.set_position_ned(
                    PositionNedYaw(cmd_x, cmd_y, cmd_z, cmd_yaw)
                )
                
                # Check if reached target
                error = ((current_pos[0]-x)**2 + 
                        (current_pos[1]-y)**2 + 
                        (current_pos[2]-target_z)**2)**0.5
                
                print(f"Position error: {error:.2f}m", end='\r')
                
                if error < 0.3:  # Reached target position
                    print("\nReached target position")
                    break

        except Exception as e:
            print(f"Movement error: {e}")
            raise
        finally:
            try:
                await self.drone.offboard.stop()
            except:
                pass
    

    async def change_altitude(self, delta):
        """Change altitude by specified delta (positive for up, negative for down)."""
        current_alt = await self.get_current_altitude()
        if current_alt is None:
            raise RuntimeError("Unable to determine current altitude")
        
        direction = "up" if delta > 0 else "down"
        print(f"Moving {direction} by {abs(delta):.2f}m")
        await self.move_to_position(0, 0, current_alt + delta)
    
    async def rotate(self, degrees, speed=25):
        """Rotate the drone by specified degrees at given speed."""
        time_needed = abs(degrees / speed) + 2  # Buffer time
        print(f"Rotating {degrees}° at {speed}°/sec...")
        
        current_yaw = await self.get_current_yaw()
        target_yaw = current_yaw + degrees
        
        await self.drone.action.set_current_speed(speed)
        await self.drone.action.goto_location(
            *await self.get_global_position(),
            target_yaw
        )
        
        await asyncio.sleep(time_needed)
    
    async def get_current_yaw(self):
        """Get current yaw angle in degrees."""
        async for attitude in self.drone.telemetry.attitude_euler():
            return attitude.yaw_deg
    
    async def wait_for_altitude(self, target, timeout=20):
        """Wait until drone reaches target altitude."""
        start_time = time.time()
        print(f"Waiting to reach {target:.2f}m...")
        
        while True:
            current = await self.get_current_altitude()
            if current is None:
                print("No altitude data received")
                await asyncio.sleep(0.1)
                continue
                
            print(f"Current altitude: {current:.2f}meter(s)", end='\r')
            
            if abs(current - target) <= self.ALTITUDE_TOLERANCE:
                print(f"\nReached target altitude: {current:.2f}m")
                return True
                
            if time.time() - start_time > timeout:
                print("\nTimeout waiting for altitude")
                return False
                
            await asyncio.sleep(0.1)

    async def execute_with_timeout(self, coro, timeout):
        """Execute a coroutine with timeout"""
        try:
            await asyncio.wait_for(coro, timeout)
        except asyncio.TimeoutError:
            print(f"Timeout exceeded for command")
            raise

    async def cleanup(self):
        """Properly cleanup all background tasks"""
        if hasattr(self, '_position_updater') and self._position_updater:
            self._position_updater.cancel()
            try:
                await self._position_updater
            except asyncio.CancelledError:
                pass
        
        if hasattr(self, '_global_position_updater') and self._global_position_updater:
            self._global_position_updater.cancel()
            try:
                await self._global_position_updater
            except asyncio.CancelledError:
                pass
            
        if hasattr(self, '_armed_updater') and self._armed_updater:
            self._armed_updater.cancel()
            try:
                await self._armed_updater
            except asyncio.CancelledError:
                pass
    
    # Implanted VC_translator

    async def VC_translator(self, command_list):
        """
        Translates a list of segmented commands into drone control function calls.
        """
        if not command_list:
            print("No command received.")
            return
        
        print("command list:", command_list)
        print()

        i = 0
        while i < len(command_list):
            command = command_list[i]
            print(command)
            # Takeoff Command
            if command == "takeoff":
                await self.takeoff()

            # Spin Command (degrees)
            elif command == "spin" or command == "rotate" and i + 1 < len(command_list):
                try:
                    degrees = (command_list[i + 1])*16
                    await self.rotate(degrees)
                    i += 1
                except ValueError:
                    print(f"Invalid angle for spin: {command_list[i+1]}")

            # Move Command (X, Y, Z altitude)
            elif command == "move" and i + 3 < len(command_list):
                try:
                    x, y, alt = float(command_list[i + 1]), float(command_list[i + 2]), float(command_list[i + 3])
                    await self.move_to_position(x, y, alt)
                    i += 3
                except ValueError:
                    print(f"Invalid move parameters: {command_list[i+1:i+4]}")

            # Land Command
            elif command == "land":
                await self.land()

            elif command == "home":
                await self.move_to_position(0, 0, self.DEFAULT_ALTITUDE)
                    

            elif command == "hold":
                pass

            elif command == "exit":
                await self.execute_with_timeout(self.land(), timeout=5)
                await self.arm_disarm(False)
                print("Exiting...")
                break

            elif command == "waypoint" and i + 1 < len(command_list):
                wp_name = command_list[i + 1].lower()
                match = get_close_matches(wp_name, WAYPOINTS.keys(), n=1, cutoff=0.6)
                if match:
                    coords = WAYPOINTS[match[0]]
                    x, y, alt = coords
                    alt = alt + 0.25
                    await self.move_to_position(x, y, alt)
                    i += 1  # Skip the waypoint name
                else:
                    print(f"Unknown waypoint: {wp_name}")
                    i += 1

            else:
                    print(f"Unknown command: {command}")
                    
            # Print position after each command
            await asyncio.sleep(2)  # Brief pause between commands
            print(f"Command Executed: {command}")
            # await self.print_position()

    

            # Other commands as needed...

            i += 1





# Main Loop
async def main():
    try:
        # Connect to Drone
        drone = DroneController(connection_string="udp://:14550")
        await drone.connect()
        print("...")
        while True:
            print("Please select a command :\n")
            print("V. Voice Command (One Instance)\n")
            print("C. Voice Command (Run Continuously)\n")
            print("T. Text-Based Command\n")
            print("F. Functions List\n")
            print("E. Exit\n")
            coms = input("Please input V, C, T, or E:")

            print()

            if coms.lower() == "v":
    
                running = True
                while running:
                    running = run_OneVCOnly(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                    await DroneController.VC_translator(drone, running)
                    running = False

            elif coms.lower() == "c":

                running = True
                while running:
                    running = run_WakeWord(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                    await DroneController.VC_translator(drone, running)

            elif coms.lower() == "t":

                command = input("Please put in a text command: ")

                segments = segment_sentence(command)

                await drone.VC_translator(segments)

                await asyncio.sleep(2)  # Use asyncio.sleep instead of time.sleep

                continue


            elif coms.lower() == "f":

                print("Takeoff: Drone becomes airborne\n")
                print("Move X Y Z: Drone moves in an x and y coordinate plane with Z being altitude \n")
                print("Waypoint: Drone moves to preset waypoints. Press 'W' to see the list of current waypoints\n")
                print()

            elif coms.lower() == "e":

                print("Goodbye!")
                print()
                break

            else:
                print("Invalid command. Please try again.\n")
                continue

    except Exception as e:
        print(f"Mission failed: {e}")
    # finally:
    #     pass
    #     print("Cleaning up...")
    #     try:
    #         await drone.cleanup()
    #         if await drone.is_armed():
    #             await drone.land()
    #             await asyncio.sleep(5)
    #             await drone.arm_disarm(False)
    #     except Exception as e:
    #         print(f"Cleanup error: {e}")

if __name__ == '__main__':
    asyncio.run(main())

