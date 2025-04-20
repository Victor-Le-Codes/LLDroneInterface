from DroneConnection import DroneConnection, DEFAULT_ALTITUDE
from difflib import get_close_matches
from re import match, sub 

class CommandParser:
    IRRELEVANT_WORDS = {"to", "by", "and", "in", "on", "at", "for", ",", ".", "space", "go", "the", "find"}

    def __init__(self, waypoints: dict[str,list[float]]):
        self.waypoints = waypoints

    def segment_sentence(self, sentence: str) -> list[str]:
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
            token = tokens[i]
            # Skip irrelevant words (e.g., 'to', 'by', 'and', etc.)
            if token in self.IRRELEVANT_WORDS:
                i += 1
                continue

            # Two-word commands
            if i + 1 < len(tokens):
                two = f"{token} {tokens[i+1]}"
                if two in {"take off", "filing cabinet", "water dispenser", "coffee machine"}:
                    processed_tokens.append(two.replace(" ", "_"))
                    i += 2
                    continue
                elif token in {"spin", "rotate", "spend"}:
                    processed_tokens.append(token)
                    i += 2
                    continue
                elif token in {"move", "fly"}:
                    processed_tokens.append("move")
                    i += 1
                    if i < len(tokens) and match(r'^-?\d+$', tokens[i]):
                        processed_tokens.append(tokens[i])
                        i += 1
                    continue
                elif token.isdigit():  # Handle other numbers as they are
                    processed_tokens.append(token)
                    i += 1
                    continue
                elif match(r'^[a-z]+$', token):  # Only word tokens (like "move")
                    processed_tokens.append(token)
                    i += 1
                    continue

            pos_num_map = {
                "zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5",
                "six":"6","seven":"7","eight":"8","nine":"9","ten":"10","eleven":"11",
                "twelve":"12","thirteen":"13","fourteen":"14","fifteen":"15",
                "sixteen":"16","seventeen":"17","eighteen":"18","nineteen":"19","twenty":"20"
            }
            if token == "negative" and i + 1 < len(tokens):
                next_token = tokens[i+1]
                if next_token in pos_num_map:
                    processed_tokens.append(f"-{pos_num_map[next_token]}")
                    i += 2
            elif token in pos_num_map:
                processed_tokens.append(pos_num_map[token])
                i += 1
            elif match(r'^-?\d+$', token):
                processed_tokens.append(token)
                i += 1
            elif match(r'^[a-z]+$', token):
                processed_tokens.append(token)
                i += 1
            # Default to just appending the token if it's not caught by any condition
            else:
                processed_tokens.append(token)
                i += 1
        return processed_tokens

    def VC_translator(self, commands: list[str], drone: DroneConnection):
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
            # Waypoint Command
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
            