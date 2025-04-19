from DroneConnection import DroneConnection, DEFAULT_ALTITUDE
from difflib import get_close_matches
from re import match, sub 

class CommandParser:
    def __init__(self, waypoints: dict[str,list[float]]):
        self.waypoints = waypoints

    def parse(self, text: str) -> list[str]:      # segment_sentence
        """
        Segments the sentence into drone actions based on recognized patterns.
        Filters out non-relevant words (like 'to', 'by', 'and', etc.) and splits multi-digit numbers,
        except for cases like 'spin', 'rotate', 'spend', etc.
        """
        # Preprocess the sentence to split multi-digit numbers into individual digits
        sentence = sub(r'(\d+)', lambda x: ' '.join(list(x.group(0))), text)
        
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
            
            # Default to just appending the token if it's not caught by any condition
            else:
                processed_tokens.append(tokens[i])
                i += 1
        
        return processed_tokens

    def execute(self, commands: list[str], drone: DroneConnection):   # VC_translator
        """Translates a list of segmented commands into drone control function calls."""
        if not commands:
            print("No command received.")
            return

        i = 0
        while i < len(commands):
            command = commands[i]
            
            # Takeoff Command
            if command == "take_off":
                drone.takeoff(DEFAULT_ALTITUDE)
            
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
            elif command == "spin" and i + 1 < len(commands):
                try:
                    drone.spin(float(commands[i + 1]))
                    i += 1
                except ValueError:
                    print(f"Invalid angle for spin: {commands[i+1]}")

            # Move Command (X, Y, Z altitude)
            elif command == "move" and i + 3 < len(commands):
                try:
                    x, y, alt = float(commands[i + 1]), float(commands[i + 2]), float(commands[i + 3])
                    drone.move(x, y, alt)
                    i += 3
                except ValueError:
                    print(f"Invalid move parameters: {commands[i+1:i+4]}")

            # Home Command (Return to home position)
            elif command == "home":
                drone.move(0, 0, DEFAULT_ALTITUDE)

            elif command == "waypoint" and i + 1 < len(commands):
                wp_name = commands[i + 1].lower()
                match = get_close_matches(wp_name, self.waypoints.keys(), n=1, cutoff=0.6)
                if match:
                    coords = self.waypoints[match[0]]
                    drone.move(*coords)
                    i += 1  # Skip the waypoint name
                else:
                    print(f"Unknown waypoint: {wp_name}")
                    i += 1

            # Land Command
            elif command == "land":
                drone.land()
            
            # Exit Command
            elif command == "exit":
                drone.land()
                drone.arm_disarm(False)
                print("Exiting...")
                break

            i += 1