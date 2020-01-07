import time
exec_times = [[]]
last = time.time()
exec_groups = []

class mytimes:

    def __init__(self):
        global last
        last = time.time()


def next_interval():
    global exec_times
    global last
    exec_times[-1].append(time.time() - last)
    last = time.time()

def delete_first():
    global exec_times
    global exec_groups
    exec_groups = []
    del exec_times[0]

def next_group():
    global exec_times
    exec_times.append([])

def form_groups():
    global exec_times
    global exec_groups
    result = []
    for i in zip(*exec_times):
        result.append(sum(i))
    exec_groups.append(result)
    exec_times = []
    pass

def add_interval(t):
    global exec_times
    exec_times[-1].append(t)
