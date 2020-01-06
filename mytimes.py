import time
exec_times = [[]]
last = time.time()

class mytimes:

    def __init__(self):
        global last
        last = time.time()


def next_interval():
    global exec_times
    global last
    exec_times[-1].append(round(time.time() - last, 2))
    last = time.time()

def next_group():
    global exec_times
    exec_times.append([])
