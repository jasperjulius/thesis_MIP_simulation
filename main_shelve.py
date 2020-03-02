# -------------------------------------------------------------------------------
# main in use, saves data to database that is automatically created with name of scenario - one db for each scenario
# can be run sequentially or in parallel (only available on windows due to MacOS constraint on multiple processes)
# -------------------------------------------------------------------------------


import sys

gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"  # path to gurobi library - has to be adjusted accordingly when running on another system
sys.path.append(gurobipath)

import time
import simulation
import scenario as sc
import global_settings
import shelve
import multiprocessing as mp
from simulation import binomial
from simulation import neg_binomial
from numpy import random as rand
from statistics import variance
import db_reader as reader
import pickle

parallel = False


def create_stats(stats):
    total_c = 0
    for i in stats:
        total_c += sum(i)

    stats_round = [[round(i, 1) for i in list] for list in stats]
    return round(total_c, 1), stats_round


def group_stats(full_stats):
    temp = [i for i in zip(*full_stats)]
    result = []
    for i in temp:
        for j in i:
            result.append(j)
    return result


# runs one scenario without using parallel processing
#   has to be used when running on MacOS, since MacOS prohibits use of multiple processes
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


# runs one scenario using parallel processing - the many simulation runs are distributed to the processes, which all add the calculated costs to the same DB for later analysis
#   doesn't run on MacOS, since MacOS prohibits python to use multiple processes - run_scenario_sequential() has to be used on MacOS
def run_scenario_parallel(scen):
    scenario = scen
    lock = mp.Lock()

    r = scenario.get_iterator()
    pool = mp.Pool(mp.cpu_count(), initializer=init, initargs=(lock, scenario))
    pool.map(execute_single_run, r)


# used to execute one single run (one combination of Rs belonging to a scenario)
def execute_single_run(current):
    global scenario
    sim = simulation.Simulation(length=scenario.length, warm_up=scenario.warm_up, stock=60,
                                high_var=scenario.high_var,
                                high_c_shortage=scenario.high_c_shortage, demands=scenario.demands,
                                distribution=scenario.distribution, L0=scenario.L0, h0=scenario.h0)
    key = str(current[0]) + ", " + str(current[1]) + ", " + str(current[2])

    sim.warehouse.R = current[0]
    sim.warehouse.retailers[0].R = current[1]
    sim.warehouse.retailers[1].R = current[2]

    # mip
    global_settings.full_batches = False
    sim.run(FIFO=False)
    value_mip = create_stats(sim.collect_statistics())
    sim.reset()

    # mip - no batch splitting
    global_settings.full_batches = True
    sim.run(FIFO=False)
    value_batch = create_stats(sim.collect_statistics())
    sim.reset()

    # fifo
    sim.run(FIFO=True)
    value_fifo = create_stats(sim.collect_statistics())
    sim.reset()

    # save result of run into database
    if parallel:
        lock.acquire()
    with shelve.open(scenario.name) as db:
        value = group_stats((value_mip, value_batch, value_fifo))
        db[key] = value
    if parallel:
        lock.release()


# function for generating stochastic demands for each retailer - was used to generate demands_high.txt, and demands_low.txt
def generate_demands(periods, high_var):
    random = []
    if not high_var:
        n = 20
        p = 0.5
        dist = binomial(n, p)
        for i in range(2):
            demand = rand.binomial(n, p, periods)
            random.append(demand)
    else:
        n = 20
        p = 2 / 3
        dist = neg_binomial(n, p)
        for i in range(2):
            demand = rand.negative_binomial(n, p, periods)
            random.append(demand)
    return random, dist


def name_gen(settings, high_var, extra=""):
    return


if __name__ == '__main__':

    scenarios = []

    # block: (L0, Li) = (2,2)
    settings1 = {"L0": 2, "Li": 2, "high_c_shortage": True, "h0": 0.05}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings1))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings1))

    settings2 = {"L0": 2, "Li": 2, "high_c_shortage": False, "h0": 0.05}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings2))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings2))

    settings3 = {"L0": 2, "Li": 2, "high_c_shortage": True, "h0": 0.1}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings3))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings3))

    settings4 = {"L0": 2, "Li": 2, "high_c_shortage": False, "h0": 0.1}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings4))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings4))


    # block: (L0, Li) = (1,3)
    settings4 = {"L0": 1, "Li": 3, "high_c_shortage": True, "h0": 0.05}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings4))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings4))

    settings5 = {"L0": 1, "Li": 3, "high_c_shortage": False, "h0": 0.05}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings5))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings5))

    settings6 = {"L0": 1, "Li": 3, "high_c_shortage": True, "h0": 0.1}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings6))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings6))

    settings7 = {"L0": 1, "Li": 3, "high_c_shortage": False, "h0": 0.1}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings7))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings7))


    # block: (L0, Li) = (3,1)
    settings8 = {"L0": 3, "Li": 1, "high_c_shortage": True, "h0": 0.05}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings8))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings8))

    settings9 = {"L0": 3, "Li": 1, "high_c_shortage": False, "h0": 0.05}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings9))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings9))

    settings10 = {"L0": 3, "Li": 1, "high_c_shortage": True, "h0": 0.1}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings10))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings10))

    settings11 = {"L0": 3, "Li": 1, "high_c_shortage": False, "h0": 0.1}
    scenarios.append(sc.Scenario("over est,", high_var=True, settings=settings11))
    scenarios.append(sc.Scenario("over est", high_var=False, settings=settings11))


    all_names = []
    for s in scenarios:
        all_names.append(s.name)
    with open("scenario_names.txt", "wb") as f:
        pass
        # pickle.dump(all_names, f)
    i = 0
    start_time = time.time()
    for scenario in scenarios:
        print("beginning scenario", i, " - hours since start:", round((time.time() - start_time) / 3600, 2), ", scen:",
              scenario.name, ", range:", scenario.getRanges())
        before = time.time()
        run_scenario_sequential(scenario)  # change to "run_scenario_sequential(scenario)" when running on MacOS
        after = time.time()
        db = shelve.open(scenario.name + " - header")
        observed_average = [round(sum(i) / len(i), 4) for i in scenario.demands]
        db["observed average"] = observed_average
        observed_variance = [round(variance(i, scenario.distribution[3]), 4) for i in scenario.demands]
        db["observed variance"] = observed_variance
        db["name"] = scenario.name
        db["L0"] = scenario.L0
        db["periods"] = scenario.length
        db["warm up"] = scenario.warm_up
        db["high var"] = scenario.high_var
        db["high c ratio"] = scenario.high_c_shortage
        db["distribution"] = scenario.distribution
        db["runtime hours"] = round((after - before) / 3600, 2)
        db.close()
        # reader.run(scenario.name)
        print("done with scenario", i, " - hours since start:", round((time.time() - start_time) / 3600, 2), ", scen:",
              scenario.name)
        i += 1
