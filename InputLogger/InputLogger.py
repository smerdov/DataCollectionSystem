from pynput import mouse, keyboard
from queue import Queue
from threading import Thread
from datetime import datetime
import json

TIME_FORMAT4FILES = '%Y-%m-%d-%H-%M-%S'
TIME_FORMAT = '%Y-%m-%d-%H:%M:%S.%f'

queue = Queue(maxsize=10000)
coord_formating = '%.2f'
current_datetime4files = datetime.now().strftime(TIME_FORMAT4FILES)
filename_mouse = f'mouse_{current_datetime4files}.csv'
filename_keyboard = f'keyboard_{current_datetime4files}.csv'
header_mouse = 'time,event,x,y,params'

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

    msg = f'{current_time},{event},{x},{y},{params_str}'
    queue.put(msg)


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

    msg = f'{current_time},{event},{x},{y},{params_str}'
    queue.put(msg)

def mouse_on_scroll(x, y, dx, dy):
    current_time = get_current_time()
    x = coord_formating % x
    y = coord_formating % y
    event = 'ms'  # mouse scroll

    params = {}
    params['dx'] = dx
    params['dy'] = dy
    params_str = json.dumps(params)

    msg = f'{current_time},{event},{x},{y},{params_str}'
    queue.put(msg)


# def



def dequeue(queue, filename):
    with open(filename, 'w') as f:
        f.write(header_mouse + '\n')

        while True:
            item = queue.get()
            f.write(item + '\n')
            f.flush()




mouse_listener = mouse.Listener(
        on_move=mouse_on_move,
        on_click=mouse_on_click,
        on_scroll=mouse_on_scroll)
mouse_listener.start()

mouse_dequeue_thread = Thread(target=dequeue, args=(queue, filename_mouse))
mouse_dequeue_thread.start()


