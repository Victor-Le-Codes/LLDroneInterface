from CommandParser import CommandParser
from DroneConnection import DroneConnection
from SpeechInterface import SpeechInterface

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

class VoiceDroneController:

    def __init__(self):
        self.drone = DroneConnection()
        self.speech = SpeechInterface()
        self.parser = CommandParser(WAYPOINTS)

    def listen_loop(self, require_wake: bool = True) -> None:
        """Continuously listen and execute until 'goodbye'."""
        running = True
        while running:
            running, tokens = self.speech.listen_for_commands(require_wake)
            if not running:
                break
            self.speech.play_audio("../Audio/GA_Voice_Command_Recognized.mp3")
            running = self.parser.VC_translator(tokens, self.drone)
