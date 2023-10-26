# TechLevelZero | 2023
#
# Mazda RX-8 Display Tilt Controller for use with stepper motors
# This Python script is designed to control the tilting mechanism of the display in a Mazda RX-8 using a stepper motor.
# The control parameters and configurations are loaded from the 'config.json' file, allowing easy customization.

# Project Overview:
# - The script manages the open and close functions of the display, as well as auto-open functionality based on tilt sensors.
# - Tilt angle adjustments are performed with a stepper motor.
# - User interaction is provided through the physical buttons.

# Configuration:
# - Please use the 'config.json' file to adjust settings and parameters to match your specific setup.

# Note: If needs be, documentation and comments are included throughout the code for better understanding and maintenance.


import time
import json
import board
import digitalio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_motor import stepper

config = {}
with open('config.json', 'r') as file:
    config = json.load(file)


print("RX-8 SatNav Display Tilt Controller")

# Mode button setup
button = DigitalInOut(getattr(board, config["buttons"]["open"]))
button.pull = Pull.UP

tilt_button = DigitalInOut(getattr(board, config["buttons"]["tilt"]))
tilt_button.pull = Pull.UP

tilt_detector = DigitalInOut(getattr(board, config["sensor"]["tilt"]))
tilt_detector.switch_to_input(pull = digitalio.Pull.UP)

mode = 0         		  	# Track state of display. (0 = closed | 1 = open)
tilt_angle = 0 			  	# Binary tilt angle to see if the screen is open or closed...roughly. (This is not accurate and is just use to self corect in case of manual opening and closing.)
auto_open_has_run = False 	# Using to see if auto open functionality has been ran and to not run again. 

##\\\\\\\\\\\\\\\\\\\\\\\\### Stepper motor setup ###\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

DELAY = config["movement"]["speed"]  # Fastest is 0.004. 0.01 is  smooth but gets jittery after that.
STEPS = 750 + config["movement"]["gain"]# this it the amount of steps for my RX-8, please look at the config file to ejust the movment

coils = (
    DigitalInOut(getattr(board, config["stepper_config"]["a1"])),  # A1
    DigitalInOut(getattr(board, config["stepper_config"]["a2"])),  # A1
    DigitalInOut(getattr(board, config["stepper_config"]["b1"])),  # A1
    DigitalInOut(getattr(board, config["stepper_config"]["b2"])),  # A1
)
for coil in coils:
    coil.direction = Direction.OUTPUT

stepper_motor = stepper.StepperMotor(
    coils[0], coils[1], coils[2], coils[3], microsteps=None
)

##\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
##\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\


##\\\\\\\\\\\\\\\\\\\\\\\\\\\\\### Open | close functions ###\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

def display_open():
    print("opening")
    for _ in range(STEPS):
        stepper_motor.onestep(style=stepper.DOUBLE, direction=stepper.FORWARD)
        time.sleep(DELAY)
    stepper_motor.release()


def display_close():
    global tilt_angle
    
    print("closing")
    for _ in range(STEPS - ((config["movement"]["tilt_angle_increment"] - 3) * tilt_angle)):
        stepper_motor.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
        time.sleep(DELAY)
    stepper_motor.release()
    tilt_angle = 0
    
##\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
##\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    
def tilt():
    global tilt_angle
    if tilt_angle is config["movement"]["total_tilt_angles"]:
        for _ in range((config["movement"]["total_tilt_angles"] - 1) * config["movement"]["tilt_angle_increment"]):
            print(tilt_angle)
            stepper_motor.onestep(style=stepper.DOUBLE, direction=stepper.FORWARD)
            time.sleep(DELAY)
        stepper_motor.release()
        tilt_angle = 0
    else:
        for _ in range(config["movement"]["tilt_angle_increment"]):
            print(tilt_angle)
            stepper_motor.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
            time.sleep(DELAY)
        stepper_motor.release()

while True:
    
    if tilt_detector.value:
        mode = 0  # Sets the mode to 0 as the display is closed according to the tilt sensor.
    else:
        mode = 1  # Sets the mode to 1 as the display is open according to the tilt sensor.
    
    ########### AUTO OPEN ######################
    if config["auto_open"]["on"]:
        if not auto_open_has_run:
            time.sleep(config["auto_open"]["delay"])
            if tilt_detector.value:
                if mode is not 1:
                    display_open()
                    mode = 1
                    auto_open_has_run = True
            else:
                mode = 1
                auto_open_has_run = True
    ############################################
    
    if not button.value:
        
        # Used to toggle between the two modes. (open and closed) [FYI: The modulo operator (%) returns the remainder. 1 divided by 2 leaves a remainder of 1 and 2 divided by 2 leaves no remainder so 0]
        mode = (mode + 1) % 2
       
        # checks to see which mode is curanly active and opens or closes the display accordingly.
        if mode is 0:
            display_close()
        elif mode is 1:
            display_open()
            
        time.sleep(0.1)  # Prevent switch bounce.
        
      # Prevent tilt from being used when the display is closed.
    if not tilt_button.value:
        if mode is 0:
            print("no tilt as closed")
            time.sleep(0.1)
        if mode is 1:
            # keeps track of the angle and resets after the defined amount of pushes.
            if tilt_angle is config["movement"]["total_tilt_angles"]:
                tilt_angle = 0
            else:          
                tilt_angle = tilt_angle + 1
                tilt()
                time.sleep(0.3)
            