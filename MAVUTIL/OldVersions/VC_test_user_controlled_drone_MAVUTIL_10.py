from pymavlink import mavutil
from speech_recognition import Microphone, Recognizer, UnknownValueError, RequestError, WaitTimeoutError
from time import sleep, time
import time
import collections
from collections.abc import MutableMapping
collections.MutableMapping = collections.abc.MutableMapping
from re import match, sub 
from difflib import get_close_matches
import pygame
import re
import sys
from pathlib import Path

WAYPOINTS = {
    "home": [0, 0, 3],
    "chair": [1, 2.5, 1.9],
    "desk": [4, 1.3, 1.3],
    "filing _cabinet": [5.5, 1, 1.2],
    "board": [4.5, -2.0, 1.6],
    "tv": [1.1, -2.9, 0.8],
    "router": [2.6, 0.3, 0.7],
    "shredder": [5.5, 1, 1.3],
    "microphone": [3.4, -1.6, 2.1],
    "water_dispenser": [2.5, -2.6, 2.5],
    "coffee_machine": [4.0, -2.9, 2],
    "cat": [-0.5, 2.6, 1]
    # Add more waypoints here
}



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


def recognize_speech():
    """Function to recognize speech using the microphone."""
    with Microphone() as source:
        print("Listening for up to 30 seconds...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=30)
            print("Captured audio, processing...")
            query = recognizer.recognize_google(audio)
            return query
        except UnknownValueError:
            print("Sorry, I couldn't understand that. Please try again.")
            return None
        except RequestError as e:
            print(f"Could not request results; {e}")
            return None
        except WaitTimeoutError:
            print("No speech detected. Please try again.")
            return None
        
# Initialize the speech recognizer
recognizer = Recognizer()

def run_WakeWord(turnOn):
    """Function to listen for the wake word and recognize commands."""
    running = True  # Flag to control the main loop
    while turnOn and running:
        # Listen for the wake word
        print("Waiting for the wake word 'Okay Steven' or 'Hey Steven...")
        wake_word_detected = False
       
        while not wake_word_detected:
            wake_prompt = recognize_speech()

            if wake_prompt == None:
                continue

            elif wake_prompt and ("okay steven") or ("hey steven") in wake_prompt.lower():
                wake_word_detected = True
                print("Wake word 'Steven' detected! Listening for your command...")
                play_audio("GA_Mic_Start.mp3")
            elif wake_prompt:
                print(f"You said: {wake_prompt}. Waiting for the wake word 'Steven'.")
            else:
                continue
       
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
            
            wake_prompt = recognize_speech()

            if wake_prompt == None:
                continue

            elif wake_prompt and ("steven") or ("hey steven") in wake_prompt.lower():
                wake_word_detected = True
                play_audio("GA_Mic_Start.mp3")
                print("Listening for your command...")
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


# Connect to the drone via TCP
connection = mavutil.mavlink_connection("tcp:127.0.0.1:5763", autoreconnect=True)

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
            sleep(5)  # Wait for the drone to arm before continuing
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
    sleep(2)
    altitude = altitude - 0.05
    wait_for_altitude(altitude, ALTITUDE_TOLERANCE)
    print("Takeoff complete.")

@arm_check_required
def land():
    """Lands the drone and waits for completion."""
    print("Landing...")
    send_nav_command(mavutil.mavlink.MAV_CMD_NAV_LAND)
    sleep(2)
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
    sleep(5)

@arm_check_required
def set_altitude(altitude):
    """Sets the target altitude for the drone."""
    print(f"Setting altitude to {altitude}m...")
    sleep(3)

@arm_check_required
def spin(degrees):
    """Rotates the drone by a specified number of degrees."""
    time_needed = (degrees / 25) + 5  # degrees/degree turn per second
    set_mode("GUIDED")
    print(f"Rotating {degrees} degrees...")
    send_nav_command(mavutil.mavlink.MAV_CMD_CONDITION_YAW, param1=degrees, param2=25, param3=1, param4=1)
    sleep(time_needed)

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
        sleep(0.1)

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
    sleep(5)  # Allow time for movement

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
    sleep(3)  # Allow time for altitude change

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
    sleep(3)  # Allow time for altitude change

# --- Command Processing ---

def segment_sentence(sentence):
    """
    Segments the sentence into drone actions based on recognized patterns.
    Filters out non-relevant words (like 'to', 'by', 'and', etc.) and splits multi-digit numbers,
    except for cases like 'spin', 'rotate', 'spend', etc.
    """
    # Preprocess the sentence to split multi-digit numbers into individual digits
    sentence = sub(r'(\d+)', lambda x: ' '.join(list(x.group(0))), sentence)
    
    # Convert the sentence to lowercase and split into tokens
    tokens = sentence.lower().split()
    
    processed_tokens = []
    i = 0
    
    while i < len(tokens):
        # Skip irrelevant words (e.g., 'to', 'by', 'and', etc.)
        if tokens[i] in ["to", "by", "and", "in", "on", "at", "for", ",", ".", "space", "go", "the", "find"]:
            i += 1
            continue
        
        if i < len(tokens) - 1:
            if tokens[i] == "take" and tokens[i+1] == "off":
                processed_tokens.append("take_off")
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
                processed_tokens.append(tokens[i])
                i += 2  # Skip the number part
                continue
            elif tokens[i] in ["move", "fly"]:  # Handle commands like move, fly
                processed_tokens.append("move")  # Treat both 'move' and 'fly' as 'move'
                i += 1  # Move to the next token
                # If the next token is a number, treat it as a whole
                if i < len(tokens) and tokens[i].isdigit():
                    processed_tokens.append(tokens[i])
                    i += 1  # Skip the number part
                continue
            elif tokens[i].isdigit():  # Handle other numbers as they are
                processed_tokens.append(tokens[i])
                i += 1
                continue
            elif match(r'^[a-z]+$', tokens[i]):  # Only word tokens (like "move")
                processed_tokens.append(tokens[i])
                i += 1
                continue

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
        
        # # Fly To Command (X, Y coordinates)
        # elif command == "fly_to" and i + 2 < len(command_list):
        #     try:
        #         x, y = float(command_list[i + 1]), float(command_list[i + 2])
        #         fly_to(x, y)
        #         i += 2
        #     except ValueError:
        #         print(f"Invalid coordinates for fly_to: {command_list[i+1:i+3]}")

        # # Go Up Command
        # elif command == "go_up" and i + 1 < len(command_list):
        #     try:
        #         go_up(float(command_list[i + 1]))
        #         i += 1
        #     except ValueError:
        #         print(f"Invalid altitude for go_up: {command_list[i+1]}")

        # # Go Down Command
        # elif command == "go_down" and i + 1 < len(command_list):
        #     try:
        #         go_down(float(command_list[i + 1]))
        #         i += 1
        #     except ValueError:
        #         print(f"Invalid altitude for go_down: {command_list[i+1]}")

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

        elif command == "waypoint" and i + 1 < len(command_list):
            wp_name = command_list[i + 1].lower()
            match = get_close_matches(wp_name, WAYPOINTS.keys(), n=1, cutoff=0.6)
            if match:
                coords = WAYPOINTS[match[0]]
                move(*coords)
                i += 1  # Skip the waypoint name
            else:
                print(f"Unknown waypoint: {wp_name}")
                i += 1




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
        while True:
            print("Please select a command :\n")
            print("V. Voice Command (One Instance)\n")
            print("C. Voice Command (Run Continuously)\n")
            print("T. Text-Based Command\n")
            print("F. Functions List\n")
            print("E. Exit\n")
            coms = input("Please input V, C, T, F, W, or E:")

            print()

            if coms.lower() == "v":
    
                running = True
                while running:
                    running = run_OneVCOnly(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                    VC_translator(running)
                    running = False

            elif coms.lower() == "c":

                running = True
                while running:
                    running = run_WakeWord(True)
                    if not running:
                        break  # Exit the loop completely when 'goodbye' is detected
                    VC_translator(running)

            elif coms.lower() == "t":

                command = input("Please put in a text command: ")

                segments = segment_sentence(command)

                VC_translator(segments)

                time.sleep(2)  # Use asyncio.sleep instead of time.sleep

                continue


            elif coms.lower() == "f":

                print("Takeoff: Drone becomes airborne\n")
                print("Move X Y Z: Drone moves in an x and y coordinate plane with Z being altitude \n")
                print("Waypoint: Drone moves to preset waypoints. Press 'W' to see the list of current waypoints\n")
                print("Land: Drone lands at its current XY position\n")
                print("Home: Drone goes to its default XY position of 0, 0 with an altitude of", DEFAULT_ALTITUDE, "\n")
                print()

            elif coms.lower() == "w":

                print(WAYPOINTS)
                print()

            elif coms.lower() == "e":

                print("Goodbye!")
                print()
                break

            else:
                print("Invalid command. Please try again.\n")
                continue
    

if __name__ == "__main__":
    print("Starting main loop...")
    main()
