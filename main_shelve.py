# -------------------------------------------------------------------------------
# old main, used for executing scenarios, and saving results of each run of scenario to excel
# replaced by main_shelve
# -------------------------------------------------------------------------------


import sys

gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
sys.path.append(gurobipath)

import simulation
import scenario as sc
import settings
import shelve
import multiprocessing as mp
from simulation import binomial
from simulation import neg_binomial
from numpy import random as rand

parallel = False


def total_costs(total_sep):
    total = 0
    for i in total_sep:
        total += sum(i)
    return total


def run_scenario_sequential(scen):
    global scenario
    scenario = scen
    r = scenario.get_iterator()
    for run in r:
        execute_single_run(run)


def init(l, s):
    global lock
    lock = l
    global scenario
    scenario = s
    global parallel
    parallel = True


def run_scenario_parallel(scen):
    scenario = scen
    lock = mp.Lock()

    r = scenario.get_iterator()
    pool = mp.Pool(mp.cpu_count(), initializer=init, initargs=(lock, scenario))
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
        # mip
        settings.no_batch_splitting = False
        sim.run(FIFO=False)
        value_mip = total_costs(sim.collect_statistics())
        sim.reset()

        # mip - no batch splitting
        settings.no_batch_splitting = True
        sim.run(FIFO=False)
        value_batch = total_costs(sim.collect_statistics())
        sim.reset()

    # fifo
    sim.run(FIFO=True)
    value_fifo = total_costs(sim.collect_statistics())
    sim.reset()

    # save result of run into database
    if parallel:
        lock.acquire()
    with shelve.open(scenario.number) as db:
        if only_fifo:
            db[key] = (value_fifo,)
        else:
            db[key] = (value_mip, value_batch, value_fifo)
    if parallel:
        lock.release()


def generate_demands(periods, high_var):
    random = []
    if not high_var:
        n = 20
        p = 0.5
        distribution = binomial(n, p)
        for i in range(2):
            random.append(rand.binomial(n, p, periods))
    else:
        n = 20
        p = 2 / 3
        distribution = neg_binomial(n, p)
        for i in range(2):
            random.append(rand.binomial(n, p, periods))
    return random, distribution


if __name__ == '__main__':
    periods = 10000
    warm_up = 100
    high_var = True
    demands, distribution = generate_demands(periods + warm_up, high_var)
    # todo: define scenarios to run here - different name for each scenario
    run_scenario_sequential(
        sc.Scenario("process0 - lets go", periods, warm_up, (10, 50), (20, 40), (20, 40), 1, 1, 1, repeat=1,
                    high_c_shortage=True, high_var=True, run_me_as=2, demands=demands,
                    distribution=distribution, fifo=False))
