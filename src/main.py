from VoiceDroneController import VoiceDroneController
from time import sleep

def main():
    ctrl = VoiceDroneController()
    while True:
        """Displays the main menu for users"""
        print("Please select a command :\n")
        print("V. Voice Command (One Instance)\n")
        print("C. Voice Command (Run Continuously)\n")
        print("T. Text-Based Command\n")
        print("F. Functions List\n")
        print("E. Exit\n")
        choice = input("Please input V, C, T, F, W, or E: ").lower()
        print()
        
        if choice == "v":
            ctrl.listen_loop(False)
        elif choice == "c":
            ctrl.listen_loop()
        elif choice == "t":
            command = input("Please put in a text command: ")
            ctrl.speech.listen_for_commands(False, command)
            sleep(2)
        elif choice == "f":
            print("Takeoff: Drone becomes airborne\n")
            print("Move X Y Z: Drone moves in an x and y coordinate plane with Z being altitude \n")
            print("Waypoint: Drone moves to preset waypoints. Press 'W' to see the list of current waypoints \n")
            print("Land: Drone lands at its current XY position \n")    
            print("Home: Drone goes to its default XY position of 0, 0 with an altitude of", ctrl.drone.DEFAULT_ALTITUDE, "\n")
        elif choice == "w":
            print(ctrl.WAYPOINTS, "\n")
        elif choice == "e":
            print("Goodbye!\n")
            break
        else:
            print("Invalid command. Please try again.\n")

if __name__ == "__main__":
    print("Starting main loop...")
    main()
