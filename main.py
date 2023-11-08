from evdev import InputDevice, categorize, ecodes
from gpiozero import LED, Servo, TonalBuzzer
import RPi.GPIO as GPIO
from time import sleep, time
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

    # leds
    led_front = LED(5)
    led_back = LED(6)
    led_left = LED(16)
    led_right = LED(26)

    # buzzer
    buzzer = TonalBuzzer(12)

    # ------------------------------------------ #

    GPIO.setmode(GPIO.BCM)

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

    def control_car_wheels(x, y):
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        left, right = 0, 0

        led_front.off()
        led_back.off()
        led_left.off()
        led_right.off()
        
        if abs(x) > 0.3:
            left = -x
            right = x
            
            if x < -0.1:
                led_left.on()
                led_right.off()
            elif x > 0.1:
                led_left.off()
                led_right.on()
        else:
            left = y
            right = y

            if y < -0.1:
                led_front.on()
                led_back.off()
            elif y > 0.1:
                led_front.off()
                led_back.on()

        left = max(-1.0, min(1.0, left))
        right = max(-1.0, min(1.0, right))

        return left, right

    def play_melody(notes = [('C4', 0.3), ('D4', 0.3), ('E4', 0.3), ('F4', 0.3), ('G4', 0.3), ('A4', 0.3), ('B4', 0.3), ('C5', 0.3)]):
        total_time = 0.0

        for note in notes:
            total_time += note[1]

        def melody():
            next = time()
            index = 0

            stop = False

            while not stop:
                if time() >= next:
                    if index < notes.__len__():
                        buzzer.play(notes[index][0])
                        next = time() + notes[index][1]
                        index += 1
                    else:
                        stop = True

            buzzer.stop()

        thread = threading.Thread(target=melody)
        thread.daemon = True
        thread.start()

        return total_time

    while True:
        update_all()

        if show_status: print_status([])
        if KEYS['start']: break

        thumb_x = (VALUES['thumbl_x'] - 126) / 126
        thumb_y = (VALUES['thumbr_y'] - 126) / 126
        gyro_x = -(VALUES['motion_x']) / 7000
        gyro_y = -(VALUES['motion_z']) / 7000

        if (thumb_x < -1.0): thumb_x = -1.0
        if (thumb_x > 1.0): thumb_x = 1.0
        if (thumb_y < -1.0): thumb_y = -1.0
        if (thumb_y > 1.0): thumb_y = 1.0

        if (gyro_x < -1.0): gyro_x = -1.0
        if (gyro_x > 1.0): gyro_x = 1.0
        if (gyro_y < -1.0): gyro_y = -1.0
        if (gyro_y > 1.0): gyro_y = 1.0

        left, right = control_car_wheels(thumb_x, thumb_y)

        if (KEYS['x']):
            left, right = control_car_wheels(gyro_x, gyro_y)

        drive_left(left)
        drive_right(right)

        if KEYS_JUST_PRESSED['select']:
            show_status = not show_status
            clear_line()
            print('[DEBUG] show_status: ' + str(show_status))
        
        if KEYS['square']:
            buzzer.stop()
        elif KEYS['down']:
            buzzer.play('C4')
        elif KEYS['left']:
            buzzer.play('D4')
        elif KEYS['up']:
            buzzer.play('E4')
        elif KEYS['right']:
            buzzer.play('F4')
        elif KEYS['l1']:
            buzzer.play('G4')
        elif KEYS['r1']:
            buzzer.play('A4')
        elif KEYS['l2']:
            buzzer.play('B4')
        elif KEYS['r2']:
            buzzer.play('C5')
        elif KEYS_JUST_RELEASED['square'] or KEYS_JUST_RELEASED['down'] or KEYS_JUST_RELEASED['left'] or KEYS_JUST_RELEASED['up'] or KEYS_JUST_RELEASED['right'] or KEYS_JUST_RELEASED['l1'] or KEYS_JUST_RELEASED['r1'] or KEYS_JUST_RELEASED['l2'] or KEYS_JUST_RELEASED['r2']:
            buzzer.stop()

        if KEYS_JUST_PRESSED['triangle']:
            play_melody()

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
