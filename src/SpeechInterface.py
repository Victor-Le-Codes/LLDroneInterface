from CommandParser import CommandParser
from pathlib import Path
from pygame import mixer
from speech_recognition import Microphone, Recognizer, UnknownValueError, RequestError, WaitTimeoutError
from time import sleep

class SpeechInterface:
    AUDIO_DIR = Path(__file__).resolve().parents[1] / "Audio"

    def __init__(self):
        mixer.init()
        self.recognizer = Recognizer()
        
    def play_audio(self, filename: str) -> None:
        """Function to play an audio file using pygame."""
        file_path = self.AUDIO_DIR / filename
        try:
            # Stop any previous audio playback
            if mixer.music.get_busy():
                mixer.music.stop()
                mixer.music.unload()

            # Load and play the new audio file
            mixer.music.load(file_path)
            mixer.music.play()

            # Wait for the playback to finish
            while mixer.music.get_busy():
                continue

            # Quit the mixer to release the file handle
            mixer.quit()
            sleep(0.2)  # Allow time for the system to release the file lock
            mixer.init()  # Reinitialize the mixer for the next playback
        except Exception as e:
            print(f"Error playing audio: {e}")
        
    def recognize_speech(self) -> str | None:
        """Function to recognize speech using the microphone."""
        with Microphone() as source:
            print("Listening for up to 30 seconds...")
            try:
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=30)
                print("Captured audio, processing...")
                query = self.recognizer.recognize_google(audio)
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

    def listen_for_commands(self, require_wake: bool = True, command: str = None) -> tuple[bool, list[str] | None]:
        """
        Unified listener: if require_wake, waits for the wake word; otherwise listens immediately.
        Returns (running_flag, segments or None).
        """
        running = True
        while running:
            # Wake-word detection if required
            if require_wake:
                print("Waiting for wake word 'Okay Steven' or 'Hey Steven'...")
                detected = False
                while not detected:
                    wake = self.recognize_speech()
                    if wake is None:
                        continue
                    if any(kw in wake.lower() for kw in ("okay steven", "okay stephen", "hey steven", "hey stephen")):
                        detected = True
                        print("Wake word detected, listening for command...")
                        self.play_audio("GA_Mic_Start.mp3")
                    else:
                        print(f"Ignored: {wake}. Awaiting wake word.")
                # once wake detected, fall through to capture command

            # Capture the actual command if needed
            if command is None:
                command = self.recognize_speech()

            if command is None:
                continue

            print(f"You said: {command}")
            self.play_audio("GA_Voice_Command_Recognized.mp3")

            # Normalize goodbye
            normalized = command.lower().replace(" ", "")
            if normalized in ("goodbye", "bye"):
                print("Goodbye! Exiting the program.")
                running = False
                return False, None

            # Segment into tokens and return
            segments = CommandParser(waypoints={}).segment_sentence(command)
            print("Segmented command:", segments)
            return True, segments

        return running, None
    