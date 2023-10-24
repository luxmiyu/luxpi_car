from evdev import InputDevice, categorize, ecodes
from gpiozero import LED, Servo
import RPi.GPIO as GPIO
from time import sleep
import os, signal

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
    'mode': False,
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

KEYS_LAST = {
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
    'mode': False,
}

VALUES_LAST = {
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

KEYS_JUST_PRESSED = {
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
    'mode': False,
}

KEYS_JUST_RELEASED = {
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
    'mode': False,
}

VALUES_DELTA = {
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

def update_keys():
    for key in KEYS.keys():
        value = KEYS[key]

        if KEYS[key] and not KEYS_LAST[key]:
            KEYS_JUST_PRESSED[key] = True
        elif not KEYS[key] and KEYS_LAST[key]:
            KEYS_JUST_RELEASED[key] = True
        else:
            KEYS_JUST_PRESSED[key] = False
            KEYS_JUST_RELEASED[key] = False
        
        KEYS_LAST[key] = value

def update_values():
    for key in VALUES.keys():
        VALUES_DELTA[key] = VALUES[key] - VALUES_LAST[key]
        VALUES_LAST[key] = VALUES[key]

def update_all():
    update_keys()
    update_values()

####################################################### LOOPS #######################################################

touch_name = "Wireless Controller Touchpad"
motion_name = "Wireless Controller Motion Sensors"
gamepad_name = "Wireless Controller"

touch_input = None
motion_input = None
gamepad_input = None

print('-------------------------------------------------------')

for i in range(0, 10):
    try:
        device = InputDevice(f'/dev/input/event{i}')
        print('[' + device.path + '] ' + device.name)

        if device.name == touch_name:
            touch_input = device
        elif device.name == motion_name:
            motion_input = device
        elif device.name == gamepad_name:
            gamepad_input = device
    except:
        continue

if not touch_input or not motion_input or not gamepad_input:
    print('[ERROR] Missing input devices')
    exit()

print('-------------------------------------------------------')
print('  touch_input path: ' + touch_input.path)
print(' motion_input path: ' + motion_input.path)
print('gamepad_input path: ' + gamepad_input.path)
print('-------------------------------------------------------')

if False:
    # names
    print(touch_input.name)
    print(motion_input.name)
    print(gamepad_input.name)

    # capabilities
    print(touch_input.capabilities())
    print(motion_input.capabilities())
    print(gamepad_input.capabilities())

def touch_loop():
    global touch_input
    global TOUCH
    global KEYS
    global VALUES
    global KEYS_LAST
    global VALUES_LAST
    global KEYS_JUST_PRESSED
    global KEYS_JUST_RELEASED
    global VALUES_DELTA

    for event in touch_input.read_loop():
        name = TOUCH[event.code]
        if not name: continue

        # EV_KEY
        if name == 'BTN_TOOL_FINGER':
            KEYS['one_finger'] = event.value == 1
        elif name == 'BTN_TOOL_DOUBLETAP':
            KEYS['two_finger'] = event.value == 1
        elif name == 'BTN_TOUCH':
            KEYS['touch'] = event.value == 1

        # EV_ABS
        elif name == 'ABS_X' and event.value != 0:
            # for some reason, the touchpad sends a lot of ABS_X events with value 0
            # this is a workaround to prevent the cursor from jumping to the left
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
            elif name == 'BTN_MODE':
                KEYS['mode'] = event.value == 1

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

def clear_line():
    LINE_CLEAR = '\x1b[2K'
    print(LINE_CLEAR, end= '\r')

last_status_length = 0

def print_status(extra = []):
    global last_status_length

    string = '[STATUS] '

    # VALUES
    string += f'motion: ({str(VALUES["motion_x"]).rjust(6)}, {str(VALUES["motion_y"]).rjust(6)}, {str(VALUES["motion_z"]).rjust(6)}) | '
    string += f'touch: ({str(VALUES["touch_x"]).rjust(4)}, {str(VALUES["touch_y"]).rjust(3)}) | '
    string += f'thumbl: ({str(VALUES["thumbl_x"]).rjust(3)}, {str(VALUES["thumbl_y"]).rjust(3)}) | '
    string += f'thumbr: ({str(VALUES["thumbr_x"]).rjust(3)}, {str(VALUES["thumbr_y"]).rjust(3)})'

    if extra.__len__() > 0:
        string += ' | ' + ' | '.join(extra)

    separator_added = False

    # KEYS
    for key in KEYS.keys():
        if KEYS[key]:
            if not separator_added:
                string += ' | '
                separator_added = True

            string += key + ' '

    print(string.ljust(last_status_length, ' '), end = '\r')
    last_status_length = string.__len__()

def main(): 
    global KEYS
    global VALUES
    global KEYS_LAST
    global VALUES_LAST
    global KEYS_JUST_PRESSED
    global KEYS_JUST_RELEASED

    print('[SYSTEM] Starting')
    
    # ------------------------------------------ #

    show_status = True

    # left motors
    in1 = 23
    in2 = 24
    en1 = 25

    # right motors
    in3 = 17
    in4 = 27
    en2 = 22

    transistorPin = 16
    transistorOn = False

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(transistorPin, GPIO.OUT)
    GPIO.output(transistorPin, GPIO.LOW)

    # left motors
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(en1, GPIO.OUT)
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)

    # right motors
    GPIO.setup(in3, GPIO.OUT)
    GPIO.setup(in4, GPIO.OUT)
    GPIO.setup(en2, GPIO.OUT)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)

    p1 = GPIO.PWM(en1, 1000)
    p1.start(75)

    p2 = GPIO.PWM(en2, 1000)
    p2.start(75)

    MAX_SPEED = 100
    MIN_SPEED = 50
    DEADZONE = 0.25

    def drive(side = "left", n = 0):
        if side == "left":
            [one, two, p] = [in1, in2, p1]
        else:
            [one, two, p] = [in3, in4, p2]

        if n > 1: n = 1
        elif n < -1: n = -1

        if n > DEADZONE:
            GPIO.output(one, GPIO.HIGH)
            GPIO.output(two, GPIO.LOW)
        elif n < -DEADZONE:
            GPIO.output(one, GPIO.LOW)
            GPIO.output(two, GPIO.HIGH)
        else:
            GPIO.output(one, GPIO.LOW)
            GPIO.output(two, GPIO.LOW)

        if n > -DEADZONE and n < DEADZONE:
            p.ChangeDutyCycle(0)
        else:
            p.ChangeDutyCycle(abs(n) * (MAX_SPEED - MIN_SPEED) + MIN_SPEED)
    
    def drive_left(n): drive("left", n)
    def drive_right(n): drive("right", n)

    # ------- START MAIN LOOP ------- #

    while True:
        update_all()

        if show_status: print_status([])
        if KEYS['start']: break
        
        left = (VALUES['thumbl_y'] - 126) / 126
        right = (VALUES['thumbr_y'] - 126) / 126

        drive_left(left)
        drive_right(right)

        if KEYS_JUST_PRESSED['select']:
            show_status = not show_status
            clear_line()
            print('[DEBUG] show_status: ' + str(show_status))
        
        if KEYS_JUST_PRESSED['mode']:
            transistorOn = not transistorOn
            GPIO.output(transistorPin, GPIO.HIGH if transistorOn else GPIO.LOW)
            clear_line()
            print('[DEBUG] transistor: ' + str(transistorOn))

    # ------- END MAIN LOOP ------- #

    os.kill(os.getpid(), signal.SIGINT)

####################################################### START #######################################################

functions = [touch_loop, motion_loop, gamepad_loop, main]

for f in functions:
    thread = threading.Thread(target=f)
    thread.daemon = True
    thread.start()

try:
    # loop forever
    while True:
        pass
except KeyboardInterrupt:
    print('\n[SYSTEM] Detected keyboard interrupt')
except Exception as e:
    print('\n[ERROR] An unexpected error occurred')
    print(e)
finally:
    clear_line()

    print('[SYSTEM] Cleaning up GPIO')
    GPIO.cleanup()

    print('[SYSTEM] Exiting')
    exit()
