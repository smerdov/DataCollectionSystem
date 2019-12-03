from pynput import mouse, keyboard
from queue import Queue
from threading import Thread
from datetime import datetime
import json
import os

TIME_FORMAT4FILES = '%Y-%m-%d-%H-%M-%S'
TIME_FORMAT = '%Y-%m-%d-%H:%M:%S.%f'
sep = ';'

queue_mouse = Queue(maxsize=10000)
queue_keyboard = Queue(maxsize=10000)
coord_formating = '%.2f'
current_datetime4files = datetime.now().strftime(TIME_FORMAT4FILES)

if not os.path.exists('data'):
    os.mkdir('data')

filename_mouse = f'data/mouse_{current_datetime4files}.csv'
filename_keyboard = f'data/keyboard_{current_datetime4files}.csv'
header_mouse = f'time{sep}event{sep}x{sep}y{sep}params'
header_keyboard = f'time{sep}event{sep}button'

def get_current_time():
    return datetime.now().strftime(TIME_FORMAT)
    # return datetime.now().timestamp()


def mouse_on_move(x, y):
    current_time = get_current_time()
    x = coord_formating % x
    y = coord_formating % y
    event = 'mm'  # mouse movement

    params = {}
    params_str = json.dumps(params)

    msg = f'{current_time}{sep}{event}{sep}{x}{sep}{y}{sep}{params_str}'
    queue_mouse.put(msg)


def mouse_on_click(x, y, button, pressed):
    current_time = get_current_time()
    x = coord_formating % x
    y = coord_formating % y

    if pressed:
        event = 'mp'  # mouse pressed
    else:
        event = 'mr'  # mouse released

    params = {}
    params['button'] = button.name
    params_str = json.dumps(params)

    msg = f'{current_time}{sep}{event}{sep}{x}{sep}{y}{sep}{params_str}'
    queue_mouse.put(msg)

def mouse_on_scroll(x, y, dx, dy):
    current_time = get_current_time()
    x = coord_formating % x
    y = coord_formating % y
    event = 'ms'  # mouse scroll

    params = {}
    params['dx'] = dx
    params['dy'] = dy
    params_str = json.dumps(params)

    msg = f'{current_time}{sep}{event}{sep}{x}{sep}{y}{sep}{params_str}'
    queue_mouse.put(msg)


def keyboard_on_press(key):
    current_time = get_current_time()
    event = 'kp'  # keyboard pressed
    if hasattr(key, 'char'):
        button_name = key.char
    else:
        button_name = key.name

    if button_name == sep:  # We won't lose much but simplify the format
        return

    msg = f'{current_time}{sep}{event}{sep}{button_name}'
    queue_keyboard.put(msg)


def keyboard_on_release(key):
    current_time = get_current_time()
    event = 'kr'  # keyboard released
    if hasattr(key, 'char'):
        button_name = key.char
    else:
        button_name = key.name

    if button_name == sep:  # We won't lose much but simplify the format
        return

    msg = f'{current_time}{sep}{event}{sep}{button_name}'
    queue_keyboard.put(msg)


def dequeue(queue, filename, header):
    with open(filename, 'w') as f:
        f.write(header + '\n')

        while True:
            item = queue.get()
            f.write(item + '\n')
            f.flush()

mouse_listener = mouse.Listener(
        on_move=mouse_on_move,
        on_click=mouse_on_click,
        on_scroll=mouse_on_scroll)
mouse_listener.start()

keyboard_listener = keyboard.Listener(
    on_press=keyboard_on_press,
    on_release=keyboard_on_release)
keyboard_listener.start()


mouse_dequeue_thread = Thread(target=dequeue, args=(queue_mouse, filename_mouse, header_mouse))
keyboard_dequeue_thread = Thread(target=dequeue, args=(queue_keyboard, filename_keyboard, header_keyboard))

mouse_dequeue_thread.start()
keyboard_dequeue_thread.start()

