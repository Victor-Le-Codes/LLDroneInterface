# Voice Command portion by Large Language Interface for Advanced Surveillance Drone

# Pretrained LLM by our mentor Richie Ryu Suganda

# You must make an account with Hugging Face and request permission to access the Meta Llama 3.2 1B Instruct model

# This code is currently running on: CPU mode

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)

from peft import PeftModel, PeftConfig
import time
from pymavlink import mavutil
from mavsdk import System, telemetry
from mavsdk.offboard import (OffboardError, PositionNedYaw, VelocityNedYaw)
import asyncio
import math
import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""

from gtts import gTTS

import time
import sys
import subprocess
import contextlib
import os
import time
import pyaudio
import pygame
import collections
from collections.abc import MutableMapping
collections.MutableMapping = collections.abc.MutableMapping
from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException
import re
from difflib import get_close_matches
import functools



from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw, VelocityBodyYawspeed
import math

from pathlib import Path

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





class DroneController:
    """A class to control a drone via MAVSDK connection."""
    
    def __init__(self, connection_string="udp://:14541"):
        """
        Initialize the drone controller with a MAVSDK connection.
        
        Args:
            connection_string: MAVSDK connection string (e.g., 'udp://:14540')
        """
        # Connection parameters
        self.drone = System()
        self.connection_string = connection_string
        self.DEFAULT_ALTITUDE = 1.0
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
    
    async def VC_translator(self, command_list):
        """
        Translates a list of command dictionaries into drone control function calls.
        
        Args:
            command_list: List of command dictionaries in the format:
                [
                    {"command": "waypoint", "x": 10.0, "y": 20.0, "z": 30.0},
                    {"command": "takeoff", "z": 5.0},
                    {"command": "land"}
                ]
        """
        if not command_list:
            print("No commands received.")
            return
        
        print("Received Commands:")
        print(command_list)

        for cmd_dict in command_list:
            try:
                command = cmd_dict["command"].lower()
                print("Executing :", cmd_dict)
                
                if command == "takeoff" or command == "take off":
                    altitude = cmd_dict["x"]
                    await self.takeoff(altitude)
                    
                elif command == "waypoint":
                    x = cmd_dict["x"]
                    y = cmd_dict["y"]
                    current_alt = await self.get_current_altitude()
                    z = cmd_dict.get("z", current_alt if current_alt is not None else self.DEFAULT_ALTITUDE)
                    await self.execute_with_timeout(self.move_to_position(x, y, z), timeout=10)
                    
                elif command == "move":
                    x = cmd_dict.get("x", 0)
                    y = cmd_dict.get("y", 0)
                    z = cmd_dict.get("z", await self.get_current_altitude())
                    await self.move_to_position(x, y, z)
                    
                elif command == "go up":
                    delta = cmd_dict["delta"]
                    await self.change_altitude(abs(delta))
                    
                elif command == "go down":
                    delta = cmd_dict["delta"]
                    await self.change_altitude(-abs(delta))
                    
                elif command == "spin":
                    degrees = cmd_dict["degrees"]
                    await self.rotate(degrees)
                    
                elif command == "home":
                    await self.move_to_position(0, 0, self.DEFAULT_ALTITUDE)
                    
                elif command == "land":
                    await self.execute_with_timeout(self.land(), timeout=5)

                elif command == "hold":
                    pass

                elif command == "exit":
                    await self.execute_with_timeout(self.land(), timeout=5)
                    await self.arm_disarm(False)
                    print("Exiting...")
                    break
                    
                else:
                    print(f"Unknown command: {command}")
                    
                # Print position after each command
                await asyncio.sleep(2)  # Brief pause between commands
                print(f"Command Executed: {command}")
                # await self.print_position()
                
            except KeyError as e:
                print(f"Missing required parameter {e} in command: {cmd_dict}")
            except Exception as e:
                print(f"Error executing command {cmd_dict}: {str(e)}")

    # Rule-based VC Translator below for faster but basic command

    async def RB_VC_translator(self, command_list):
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

            # Rotate Command (degrees)
            elif command == "spin" or command == "rotate" and i + 1 < len(command_list):
                try:
                    degrees = float(command_list[i + 1])
                    await self.rotate(degrees)
                    i += 1
                except ValueError:
                    print(f"Invalid angle for rotate: {command_list[i+1]}")

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

            else:
                    print(f"Unknown command: {command}")
                    
            # Print position after each command
            await asyncio.sleep(2)  # Brief pause between commands
            print(f"Command Executed: {command}")
            # await self.print_position()

    

            # Other commands as needed...

            i += 1
    
    # --- Flight Movement Methods ---
    
    async def takeoff(self, altitude=None):
        """Execute takeoff to specified altitude"""
        print("Starting takeoff sequence...")
        
        altitude = float(altitude) if altitude is not None else self.DEFAULT_ALTITUDE
    
        if not await self.is_armed():
            print("Running pre-arm checks...")
            if not await self.pre_arm_checks():
                raise RuntimeError("Pre-arm checks failed")
                
            print("Arming drone...")
            await self.arm_disarm(True)
            await asyncio.sleep(2)  # Give time for arming to complete
        
        print(f"Setting takeoff altitude to {altitude}m...")
        await self.drone.action.set_takeoff_altitude(altitude)
        
        print("Initiating takeoff...")
        await self.drone.action.takeoff()
        
        print("Waiting to reach target altitude...")
        await self.wait_for_altitude(altitude)
        print("Takeoff complete")

    async def land(self):
        """Execute landing sequence."""
        print("Landing...")
        await self.drone.action.land()
        await self.wait_for_altitude(0)
        print("Landing complete")
    
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
    
    async def rotate(self, degrees, speed=30):
        """
        Rotates the drone in place by sending yaw rate commands with zero velocity.
        This avoids any linear drift.
        """
        print(f"Rotating {degrees}° at {speed}°/s...")

        # Calculate time needed
        direction = 1 if degrees >= 0 else -1
        yaw_rate = speed * direction
        duration = abs(degrees) / speed
        interval = 0.1
        total_loops = int(duration / interval)

        try:
            await self.drone.offboard.set_velocity_body(
                VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0)
            )
            await self.drone.offboard.start()
        except Exception as e:
            print(f"[Rotate] Offboard already active or error: {e}")

        for _ in range(total_loops):
            await self.drone.offboard.set_velocity_body(
                VelocityBodyYawspeed(0.0, 0.0, 0.0, yaw_rate)
            )
            await asyncio.sleep(interval)

        # Stop any yaw motion
        await self.drone.offboard.set_velocity_body(
            VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0)
        )
        print(f"{degrees}° Rotation complete.")
    
    
    async def get_current_yaw(self):
        """Get current yaw angle in degrees."""
        async for attitude in self.drone.telemetry.attitude_euler():
            return attitude.yaw_deg
    
    async def wait_for_altitude(self, target, timeout=10):
        """Wait until drone reaches target altitude."""
        start_time = time.time()
        print(f"Waiting to reach {target:.2f}m...")
        
        while True:
            current = await self.get_current_altitude()
            if current is None:
                print("No altitude data received")
                await asyncio.sleep(0.1)
                continue
                
            print(f"Current altitude: {current:.2f}m", end='\r')
            
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


"""
landmarks:
table: 0.45 -2.83 2.40
chair: 1.01 2.45 1.91
desk: 4.03 1.27 1.33
filing cabinet: 5.64 0.70 1.22
board: 4.46 -2.03 1.59
TV screen: 1.05 -2.94 0.81
router: 2.64 0.34 0.73
shredder: 5.38 0.98 1.29
microphone: 3.41 -1.57 2.07
water dispenser: 2.49 -2.60 2.49
coffee machine: 4.01 -2.89 1.94
cat: -0.43 2.61 0.81
"""

# Added drone = command for other defined functions for VC control
drone = DroneController(connection_string="udp://:14550")

test_command = "take off find the tv and the cat and land"

# Initialize pygame mixer
pygame.mixer.init()

# pygame added for sound effects:
AUDIO_DIR = Path(__file__).resolve().parents[1] / "Audio"

def play_audio(filename):
    """Function to play an audio file using pygame."""
    file_path = AUDIO_DIR / filename
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




def generate_waypoint(
    command="take off, and go find the board, and cat then land.",
    max_length=384,
    drone_state="disarmed",
    drone_location=[0.0, 0.0, 0.0],
    map_data="""
    landmarks:
    table: 0.45 -2.83 2.40
    chair: 1.01 2.45 1.91
    desk: 4.03 1.27 1.33
    filing cabinet: 5.64 0.70 1.22
    board: 2.46 -0.03 1.59
    TV screen: 1.05 -2.94 0.81
    router: 2.64 0.34 0.73
    shredder: 5.38 0.98 1.29
    microphone: 3.41 -1.57 2.07
    water dispenser: 2.49 -2.60 2.49
    coffee machine: 4.01 -2.89 1.94
    cat: 1.43 0.61 0.81"""
):

    prompt = command + "\n" + "drone: " + drone_state + "\n" + "position: " + f"{drone_location[0]} {drone_location[1]} {drone_location[2]}\n" + map_data
    prompt123 = """take off, and go find the board, and cat then land.
    drone: disarmed
    position: 0.0 0.0 0.0
    landmarks:
    table: 0.45 -2.83 2.40
    chair: 1.01 2.45 1.91
    desk: 4.03 1.27 1.33
    filing cabinet: 5.64 0.70 1.22
    board: 2.46 -0.03 1.59
    TV screen: 1.05 -2.94 0.81
    router: 2.64 0.34 0.73
    shredder: 5.38 0.98 1.29
    microphone: 3.41 -1.57 2.07
    water dispenser: 2.49 -2.60 2.49
    coffee machine: 4.01 -2.89 1.94
    cat: 1.43 0.61 0.81"""

    # Create prompt
    input_text = (
        "### Instruction: Given landmarks and robot state, generate a navigation path sequence\n"
        f"### Input:\n{prompt}\n"
        "### Response:\n"
    )
    
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=768).to("cpu")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.95,
            top_p=0.99,
            do_sample=True,
        )
    
    # Extract and clean the response
    full_text =tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = full_text.split("### Response:")[-1].strip()
    if "### End" in response:
        response = response.split("### End")[0].strip()
    print(response)
    return response

def parse_commands(data):
    commands = []
    for line in data.strip().split('\n'):
        parts = line.split()
        if not parts:
            continue

        command = {"command": parts[0]}

        # Try to parse x, y, z if they exist
        if len(parts) > 1:
            try:
                command["x"] = float(parts[1])
            except ValueError:
                pass  # Ignore if conversion fails

        if len(parts) > 2:
            try:
                command["y"] = float(parts[2])
            except ValueError:
                pass

        if len(parts) > 3:
            try:
                command["z"] = float(parts[3])
            except ValueError:
                pass

        commands.append(command)

    return commands


async def parseLLM(coms, drone):
    local_pos = await drone.get_position()
    if local_pos:
        x, y, z = local_pos
        return parse_commands(generate_waypoint(command=coms, drone_location=[x, y, z]))
    return parse_commands(generate_waypoint(command=coms))



# Adding Voice Command Code Here

def run_WakeWord(turnOn):
    """Function to listen for the wake word and recognize commands."""
    running = True  # Flag to control the main loop
    while turnOn and running:
        # Listen for the wake word
        print("Waiting for the wake word 'Okay Steven' or 'Hey Steven'...")
        wake_word_detected = False
       
        while not wake_word_detected:
            wake_prompt = recognize_speech()

            if wake_prompt == None:
                continue

            elif wake_prompt and ("ok steven") or ("hey steven") in wake_prompt.lower():
                wake_word_detected = True
                print("Wake word 'Steven' detected! Listening for your command...")
                play_audio("GA_Mic_Start.mp3")
                
            elif wake_prompt:
                print(f"You said: {wake_prompt}. Waiting for the wake word 'Steven'.")
       
        # Once the wake word is detected, listen for a command
        coms = recognize_speech()
        if coms is None:
            continue  # Retry if no valid speech input was detected

        # Print the recognized command
        print(f"You said: {coms}")

        play_audio("GA_Voice_Command_Recognized.mp3")

        def normalize_goodbye(uin):
            normalized = uin.lower().replace(" ", "")  # Converts "Good bye" -> "goodbye"
            return "goodbye" if normalized in ["goodbye", "bye"] else uin

        coms = normalize_goodbye(coms)

        # Check for exit condition
        if coms.lower() == "goodbye":
            print("Goodbye! Exiting the program.")
            running = False  # Set the running flag to False to exit the loop
            break

        else:
            return coms.lower()

    return running  # Return the status of the running flag


def run_OneVCOnly(turnOn):

    """Function to listen for the wake word and recognize commands."""
    running = True  # Flag to control the main loop
    while turnOn and running:
        # Listen for the wake word
        # print("Waiting for the wake word 'Okay Steven' or 'Hey Steven'...")
        wake_word_detected = True
       
        while not wake_word_detected:
            
            wake_prompt = recognize_speech()

            if wake_prompt == None:
                continue

            elif wake_prompt and ("steven") or ("hey steven") in wake_prompt.lower():
                wake_word_detected = True
                print("Wake word 'Steven' detected! Listening for your command...")
            elif wake_prompt:
                print(f"You said: {wake_prompt}. Waiting for the wake word 'Steven'.")
       
        # Once the wake word is detected, listen for a command
        play_audio("GA_Mic_Start.mp3")
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
            return command.lower()

    return running  # Return the status of the running flag



def recognize_speech():
    """Function to recognize speech using the microphone."""
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=30)
            print("Captured audio, processing...")
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



def RB_segment_sentence(sentence):
    # Segments the sentence into drone actions based on recognized patterns.
    # Filters out non-relevant words (like 'to', 'by', 'and', etc.) and splits multi-digit numbers,
    # except for cases like 'spin', 'rotate', 'spend', etc.
    # Preprocess the sentence to split multi-digit numbers into individual digits
    # sentence = re.sub(r'(\d+)', lambda x: ' '.join(list(x.group(0))), sentence)
    
    # Convert the sentence to lowercase and split into tokens
    tokens = sentence.lower().split()
    
    processed_tokens = []
    i = 0
    
    while i < len(tokens):
        # Skip irrelevant words (e.g., 'to', 'by', 'and', etc.)
        if tokens[i] in ["to", "by", "and", "in", "on", "at", "for", ",", ".", "space", "go", "the", "find"]:
            i += 1
            continue

        # Processes potential two-worded tokens and other alternative words
        
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

    print(processed_tokens)    
    
    return processed_tokens

    

async def main():
    try:
        # Connect to Drone
        drone = DroneController(connection_string="udp://:14550")
        await drone.connect()
        # await drone.drone.action.arm()
        print("...")
        while True:
            print("Please select a command :\n")
            print("------- Single Command Actions -------")
            print("L. Land")
            print("TO. Take Off")
            print("S. Single Actions Command Mode (Continuous)")
            print()
            print("------- LLM-Based Inputs -------")
            print("V. Voice Command (One Instance)")
            print("C. [BETA] Voice Command (Run Continuously)")
            print("T. Text-Based Command")
            print()
            print("------- Rule-Based (RB) Input -------")
            print("RBV. Rule-based Voice Command")
            print("RBT. Rule-based Text Command")
            print()
            print("------- Information and Testing -------")
            print("F. Functions List")
            print("W. Waypoint List")
            print("Test. Test String")
            # print("E. Exit\n")
            print()
            i_coms = input("Please enter a corresponding letter(s) or Test:")

            print()

            if i_coms.lower() == "l":

                await drone.land()

                continue

            elif i_coms == "to":
                print(f"Current Default Altitude: {drone.DEFAULT_ALTITUDE}\n")
                t_alt = input("Please enter an altitude in meters (or hit enter for Default Altitude): ")
                print()
                
                if t_alt == "":
                    t_alt = drone.DEFAULT_ALTITUDE

                else:
                    t_alt = t_alt

                t_alt = float(t_alt)

                await drone.takeoff(t_alt)

                continue

            elif i_coms.lower() == "s":

                sc_exit = False

                while sc_exit == False:

                    print()
                    print("Please select a single drone action:\n")
                    print()
                    print(f"TO. Takeoff with Default Altitude = {drone.DEFAULT_ALTITUDE}")
                    print("L. Land Drone")
                    print("M. Move to X by Y by Z")
                    print("R. Rotate on the Z-axis via degree measurement")
                    print(f"H. Home (Go back to 0, 0, {drone.DEFAULT_ALTITUDE})")
                    print("E. Exit Single Command List and Return to Main Interface")

                    print()

                    sc_coms = input("Please enter a corresponding letter: ")
                    print()

                    sc_coms = sc_coms.lower()

                    if sc_coms == "e":

                        print()
                        print("Exiting the Single Actions Command Mode.\n")
                        print()
                        sc_exit = True

                    elif sc_coms == "to":
                        print(f"Current Default Altitude: {drone.DEFAULT_ALTITUDE}\n")
                        t_alt = input("Please enter an altitude in meters (or hit enter for Default Altitude): ")
                        print()
                        
                        if t_alt == "":
                            t_alt = drone.DEFAULT_ALTITUDE

                        else:
                            t_alt = t_alt

                        t_alt = float(t_alt)

                        await drone.takeoff(t_alt)

                        continue

                    elif sc_coms == "l":
                        print()
                        await drone.land()
                        print()
                        continue

                    elif sc_coms == "m":
                        print()
                        print("Please enter each coordinate individually:\n")
                        x_coord = input("X-Coordinate:")
                        print()
                        y_coord = input("Y-Coordinate:")
                        print()
                        z_alt = input("Z-Coordinate:")
                        print()

                        x_coord = float(x_coord)
                        y_coord = float(y_coord)
                        z_alt = float(z_alt)

                        await drone.move_to_position(x_coord, y_coord, z_alt)
                        print()

                        continue

                    elif sc_coms == "r":

                        print()

                        sc_rotate = input("Please enter a degree value from 0 to 360 Degrees: ")

                        sc_rotate = float(sc_rotate)

                        print()
                        print("Default Rotation Speed: 30°/s")

                        sc_r_speed = input("Please enter a rotational speed, pr enter for default value: ")

                        if sc_r_speed == "":

                            sc_r_speed = 30

                        else:

                            sc_r_speed = sc_r_speed

                        sc_r_speed = float(sc_r_speed)

                        await drone.rotate(sc_rotate, sc_r_speed)

                        print()

                        continue

                    elif sc_coms == "h":
                        print()
                        await drone.move_to_position(0, 0, drone.DEFAULT_ALTITUDE)
                        print()
                        continue

                    else:

                        print()
                        print("Invalid Command. Please try again.")
                        print()
                        continue

                        


            elif i_coms.lower() == "v":
    
                running = True
                while running:
                    running = run_OneVCOnly(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                    coms = running
                    waypoints = await parseLLM(coms, drone)
                    print(waypoints)
                    await drone.VC_translator(waypoints)
                    running = False

                continue

            elif i_coms.lower() == "c":

                running = True
                while running:
                    running = run_WakeWord(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                
                    coms = running
                    waypoints = await parseLLM(coms, drone)
                    print(waypoints)
                    await drone.VC_translator(waypoints)

                    continue

            elif i_coms.lower() == "t":

                coms = input("Input drone commands :")
                waypoints = await parseLLM(coms, drone)

                print(waypoints)
            
                await drone.VC_translator(waypoints)

                continue

            elif i_coms.lower() == "rbt":

                coms = input("Please put in a RB text command: ")

                segments = RB_segment_sentence(coms.lower())

                await drone.RB_VC_translator(segments)

                await asyncio.sleep(2)  # Use asyncio.sleep instead of time.sleep

                continue

            elif i_coms.lower() == "rbv":
    
                running = True
                while running:
                    running = run_OneVCOnly(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                    
                    coms = running

                    segments = RB_segment_sentence(coms.lower())

                    await drone.RB_VC_translator(segments)
                    running = False

                continue


            elif i_coms.lower() == "test":

                coms = test_command
                waypoints = await parseLLM(coms, drone)

                print(waypoints)
            
                await drone.VC_translator(waypoints)

                continue


            elif i_coms.lower() == "f":

                print("Takeoff: Drone becomes airborne\n")
                print("Move X Y Z: Drone moves in an x and y coordinate plane with Z being altitude \n")
                print("Waypoint: Drone moves to preset waypoints. Press 'W' to see the list of current waypoints\n")
                print("[BETA] Rotate: Drone rotates in place for a desired yaw degree. Works in simulation, but it may spin in a circle and drifts away for a moment before proceeding with the next command.\n")
                print("Land: Drone lands at its current XY position\n")
                print("Home: Drone goes to its default XY position of 0, 0 with an altitude of", drone.DEFAULT_ALTITUDE, "\n")
                print("Test: Test commands =", test_command, "\n")
                print()

                continue


            # elif coms.lower() == "e":

            #     print("Goodbye!")
            #     print()
            #     break

            elif i_coms.lower() == "w":

                
                print("landmarks:")
                print("table: 0.45 -2.83 2.40")
                print("chair: 1.01 2.45 1.91")
                print("desk: 4.03 1.27 1.33")
                print("filing cabinet: 5.64 0.70 1.22")
                print("board: 2.46 -0.03 1.59")
                print("TV screen: 1.05 -2.94 0.81")
                print("router: 2.64 0.34 0.73")
                print("shredder: 5.38 0.98 1.29")
                print("microphone: 3.41 -1.57 2.07")
                print("water dispenser: 2.49 -2.60 2.49")
                print("coffee machine: 4.01 -2.89 1.94")
                print("cat: 1.43 0.61 0.81")

                continue
            


            else:
                print("Invalid command. Please try again.\n")
                continue

    except Exception as e:
        print(f"Mission failed: {e}")
    finally:
        print("Cleaning up...")
        try:
            await drone.cleanup()
            if await drone.is_armed():
                await drone.land()
                await asyncio.sleep(5)
                await drone.arm_disarm(False)
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == '__main__':
    # Configuration
    MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"
    PEFT_MODEL_PATH = "./results_quants64/final_lora_adapters"  # Path to saved LoRA adapters

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model and tokenizer

    print("Loading model...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token

    # Load the base model on CPU (no quantization)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="cpu",
        torch_dtype=torch.float32  # must be float32 for CPU
    )

    # Load LoRA adapter (must match CPU device)
    model = PeftModel.from_pretrained(model, PEFT_MODEL_PATH)

    # Now run your main loop
    asyncio.run(main())

