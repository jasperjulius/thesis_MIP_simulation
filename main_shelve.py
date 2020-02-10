import simulation
import time
import openpyxl
import r as rgen
from math import trunc
import mytimes
import settings
import multiprocessing as mp
import shelve
import multiprocessing as mp

def total_costs(total_sep):
    total = 0
    for i in total_sep:
        total += sum(i)
    return total


scenario = None
lock = None

def run_scenario(scen):
    global scenario
    scenario = scen
    r = scenario.get_r()
    for run in r:
        execute_single_run(run)

def run_scenario_parallel(scen):
    global scenario
    scenario = scen
    global lock
    lock = mp.Lock()
    r = scenario.get_r()
    pool = mp.Pool(mp.cpu_count())
    pool.map(execute_single_run, r)

    def mip(elem):
        return elem[1][0]

    db = shelve.open(scenario.number)
    list = []
    for k in db.keys():
        list.append((k, db[k]))
    list.sort(key=mip)
    for i in list:
        print(i)
    pass
    db.close()

def execute_single_run(current):
    global scenario
    # simulation object needed, next() from iterator needed
    only_fifo = scenario.fifo
    sim = simulation.Simulation(length=scenario.length, warm_up=scenario.warm_up, stock=60,
                                high_var=scenario.high_var,
                                high_c_shortage=scenario.high_c_shortage, demands=scenario.demands,
                                distribution=scenario.distribution)
    print(current)
    print(round(((current[3] / scenario.duration) * 100), 2), "%")
    key = str(current[0]) + ", " + str(current[1]) + ", " + str(current[2])

    sim.warehouse.R = current[0]
    sim.warehouse.retailers[0].R = current[1]
    sim.warehouse.retailers[1].R = current[2]
    if not only_fifo:
        settings.no_batch_splitting = False
        sim.run(FIFO=False)
        value_mip = total_costs(sim.collect_statistics())
        # save results to shelve
        sim.reset()

        settings.no_batch_splitting = True
        sim.run(FIFO=False)
        value_batch = total_costs(sim.collect_statistics())
        sim.reset()

    sim.run(FIFO=True)
    value_fifo = total_costs(sim.collect_statistics())
    sim.reset()
    lock.acquire()
    with shelve.open(scenario.number) as db:
        if only_fifo:
            db[key] = (value_fifo,)
        else:
            db[key] = (value_mip, value_batch, value_fifo)
    lock.release()


