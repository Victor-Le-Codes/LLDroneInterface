from speech_recognition import Microphone, Recognizer, UnknownValueError, RequestError, WaitTimeoutError

class SpeechInterface:

    def __init__(self):
        self.recognizer = Recognizer()

    def listen(self, timeout=2, phrase_limit=30) -> str | None: # recognize_speech()
        """Function to recognize speech using the microphone."""
        with Microphone() as source:
            print("Listening for up to 30 seconds...")
            try:
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=30)
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
        
    def listen_for_wake(self) -> str:    # run_WakeWord()
        """Function to listen for the wake word."""
        while True:
            print("Waiting for the wake word 'Steven'...")
            wake_prompt = self.listen()
            if wake_prompt and ("steven" or "stephen" or "hey steven" or "hey stephen") in wake_prompt.lower():
                print("Wake word 'Steven' detected! Listening for your command...")
                return wake_prompt
            elif wake_prompt:
                print(f"You said: {wake_prompt}. Waiting for the wake word 'Steven'.")
    
    def listen_for_command(self) -> str | None:
        """Function to listen for the recognize commands."""
        print("Listening for command…")
        return self.listen()
    