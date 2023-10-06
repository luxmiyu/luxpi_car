from evdev import InputDevice, categorize, ecodes
from gpiozero import LED, Servo
import RPi.GPIO as GPIO
from time import sleep
import os
import signal

import threading

####################################################### GLOBALS #######################################################

TOUCH = {
    # EV_KEY
    272: 'BTN_LEFT',
    325: 'BTN_TOOL_FINGER',
    330: 'BTN_TOUCH',
    333: 'BTN_TOOL_DOUBLETAP',

    # EV_ABS
    0: 'ABS_X',
    1: 'ABS_Y',
    47: 'ABS_MT_SLOT',
    53: 'ABS_MT_POSITION_X',
    54: 'ABS_MT_POSITION_Y',
    57: 'ABS_MT_TRACKING_ID',
}

MOTION = {
    # EV_ABS
    0: 'ABS_X',
    1: 'ABS_Y',
    2: 'ABS_Z',
    3: 'ABS_RX',
    4: 'ABS_RY',
    5: 'ABS_RZ',
}

GAMEPAD = {
    # EV_KEY
    304: 'BTN_SOUTH',
    305: 'BTN_EAST',
    307: 'BTN_NORTH',
    308: 'BTN_WEST',
    310: 'BTN_TL',
    311: 'BTN_TR',
    312: 'BTN_TL2',
    313: 'BTN_TR2',
    314: 'BTN_SELECT',
    315: 'BTN_START',
    316: 'BTN_MODE',
    317: 'BTN_THUMBL',
    318: 'BTN_THUMBR',

    # EV_ABS
    0: 'ABS_X',
    1: 'ABS_Y',
    2: 'ABS_Z',
    3: 'ABS_RX',
    4: 'ABS_RY',
    5: 'ABS_RZ',
    16: 'ABS_HAT0X', # 0 is neutral, -1 is left and 1 is right
    17: 'ABS_HAT0Y', # 0 is neutral, -1 is up and 1 is down
}

KEYS = {
    # touch
    'one_finger': False,
    'two_finger': False,
    'touch': False,

    # gamepad
    'up': False,
    'down': False,
    'left': False,
    'right': False,
    'l1': False,
    'l2': False,
    'l3': False,
    'r1': False,
    'r2': False,
    'r3': False,
    'x': False,
    'circle': False,
    'triangle': False,
    'square': False,
    'start': False,
    'select': False,
}

VALUES = {
    'touch_x': 0,
    'touch_y': 0,
    'motion_x': 0,
    'motion_y': 0,
    'motion_z': 0,
    'motion_rx': 0,
    'motion_ry': 0,
    'motion_rz': 0,
    'thumbl_x': 0,
    'thumbl_y': 0,
    'thumbr_x': 0,
    'thumbr_y': 0,
}

####################################################### LOOPS #######################################################

touch_input = None
motion_input = None
gamepad_input = None

try:
    touch_input = InputDevice('/dev/input/event2')
    motion_input = InputDevice('/dev/input/event3')
    gamepad_input = InputDevice('/dev/input/event4')
except:
    print('Error: could not find devices')
    exit()

if False:
    print(touch_input.capabilities())
    print(motion_input.capabilities())
    print(gamepad_input.capabilities())

def touch_loop():
    global touch_input
    global TOUCH
    global VALUES
    global KEYS

    for event in touch_input.read_loop():
        name = TOUCH[event.code]
        if not name: continue

        if event.type == ecodes.EV_KEY:
            if name == 'BTN_TOOL_FINGER':
                KEYS['one_finger'] = event.value == 1
            elif name == 'BTN_TOOL_DOUBLETAP':
                KEYS['two_finger'] = event.value == 1
            elif name == 'BTN_TOUCH':
                KEYS['touch'] = event.value == 1

        elif event.type == ecodes.EV_ABS:
            if name == 'ABS_X':
                VALUES['touch_x'] = event.value
            elif name == 'ABS_Y':
                VALUES['touch_y'] = event.value

def motion_loop():
    global motion_input
    global MOTION
    global VALUES
    global KEYS

    for event in motion_input.read_loop():
        name = MOTION[event.code]
        if not name: continue

        if event.type == ecodes.EV_ABS:
            if name == 'ABS_X':
                VALUES['motion_x'] = event.value
            elif name == 'ABS_Y':
                VALUES['motion_y'] = event.value
            elif name == 'ABS_Z':
                VALUES['motion_z'] = event.value
            elif name == 'ABS_RX':
                VALUES['motion_rx'] = event.value
            elif name == 'ABS_RY':
                VALUES['motion_ry'] = event.value
            elif name == 'ABS_RZ':
                VALUES['motion_rz'] = event.value

def gamepad_loop():
    global gamepad_input
    global GAMEPAD
    global VALUES
    global KEYS

    for event in gamepad_input.read_loop():
        name = GAMEPAD[event.code]
        if not name: continue

        if event.type == ecodes.EV_KEY:
            if name == 'BTN_SOUTH':
                KEYS['x'] = event.value == 1
            elif name == 'BTN_EAST':
                KEYS['circle'] = event.value == 1
            elif name == 'BTN_NORTH':
                KEYS['triangle'] = event.value == 1
            elif name == 'BTN_WEST':
                KEYS['square'] = event.value == 1
            elif name == 'BTN_TL':
                KEYS['l1'] = event.value == 1
            elif name == 'BTN_TR':
                KEYS['r1'] = event.value == 1
            elif name == 'BTN_TL2':
                KEYS['l2'] = event.value == 1
            elif name == 'BTN_TR2':
                KEYS['r2'] = event.value == 1
            elif name == 'BTN_SELECT':
                KEYS['select'] = event.value == 1
            elif name == 'BTN_START':
                KEYS['start'] = event.value == 1

        elif event.type == ecodes.EV_ABS:
            if name == 'ABS_HAT0X':
                KEYS['left'] = event.value == -1
                KEYS['right'] = event.value == 1
            elif name == 'ABS_HAT0Y':
                KEYS['up'] = event.value == -1
                KEYS['down'] = event.value == 1
            elif name == 'ABS_X':
                VALUES['thumbl_x'] = event.value
            elif name == 'ABS_Y':
                VALUES['thumbl_y'] = event.value
            elif name == 'ABS_RX':
                VALUES['thumbr_x'] = event.value
            elif name == 'ABS_RY':
                VALUES['thumbr_y'] = event.value
            elif name == 'ABS_Z':
                KEYS['l3'] = event.value == 1
            elif name == 'ABS_RZ':
                KEYS['r3'] = event.value == 1

####################################################### MAIN LOOP #######################################################

def print_status(extra = []):
    string = ''

    # VALUES
    string += f'motion: ({str(VALUES["motion_x"]).rjust(6)}, {str(VALUES["motion_y"]).rjust(6)}, {str(VALUES["motion_z"]).rjust(6)}) | '
    string += f'touch: ({str(VALUES["touch_x"]).rjust(4)}, {str(VALUES["touch_y"]).rjust(3)}) | '
    string += f'thumbl: ({str(VALUES["thumbl_x"]).rjust(3)}, {str(VALUES["thumbl_y"]).rjust(3)}) | '
    string += f'thumbr: ({str(VALUES["thumbr_x"]).rjust(3)}, {str(VALUES["thumbr_y"]).rjust(3)}) | '

    if extra.__len__() > 0:
        string += ' | '.join(extra) + ' | '

    # KEYS
    for key in KEYS.keys():
        if KEYS[key]:
            string += key + ' '

    print(string)

def main(): 
    global KEYS
    global VALUES

    show_status = False

    in1 = 23
    in2 = 24
    en = 25

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(en, GPIO.OUT)
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)

    p = GPIO.PWM(en, 1000)
    p.start(75)

    MAX_SPEED = 100
    MIN_SPEED = 50

    def update_speed(analog):
        analog_abs = abs(analog - 126)

        if analog_abs < 10:
            p.ChangeDutyCycle(MIN_SPEED)
        
        speed = int((analog_abs / 126) * (MAX_SPEED - MIN_SPEED) + MIN_SPEED)

        if speed > MAX_SPEED:
            speed = MAX_SPEED
        elif speed < MIN_SPEED:
            speed = MIN_SPEED

        p.ChangeDutyCycle(speed)

    while True:
        if show_status: print_status()
        
        y = VALUES['thumbr_y']
        deadzone = 16

        if y > 126 + deadzone:
            update_speed(y)
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
        elif y < 126 - deadzone:
            update_speed(y)
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
        else:
            p.ChangeDutyCycle(0)
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)

        if KEYS['select']:
            show_status = not show_status

            if show_status:
                print('Showing status...')
            else:
                print('Hiding status...')

        if KEYS['start']:
            break

    os.kill(os.getpid(), signal.SIGINT)

####################################################### START #######################################################

functions = [touch_loop, motion_loop, gamepad_loop, main]

for f in functions:
    thread = threading.Thread(target=f)
    thread.setDaemon(True)
    thread.start()

try:
    while True: pass
except KeyboardInterrupt:
    print('KeyboardInterrupt: exiting...')
except:
    print('Error: unknown exception')
finally:
    print('Cleaning up GPIO...')
    GPIO.cleanup()
    exit()
