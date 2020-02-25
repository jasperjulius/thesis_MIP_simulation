# -------------------------------------------------------------------------------
# main in use, saves data to database that is automatically created with name of scenario - one db for each scenario
# can be run sequentially or in parallel (only available on windows due to MacOS constraint on multiple processes)
# -------------------------------------------------------------------------------


import sys

gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
sys.path.append(gurobipath)

import time
import simulation
import scenario as sc
import settings
import shelve
import multiprocessing as mp
from simulation import binomial
from simulation import neg_binomial
from numpy import random as rand
from statistics import variance
import db_reader as reader
import pickle

parallel = False


def total_costs(total_sep):
    total = 0
    for i in total_sep:
        total += sum(i)
    return total


def create_stats(stats):
    total_c = total_costs(stats)
    stats_round = [[round(i, 1) for i in list] for list in stats]
    return round(total_c, 1), stats_round


def group_stats(full_stats):
    temp = [i for i in zip(*full_stats)]
    result = []
    for i in temp:
        for j in i:
            result.append(j)
    return result


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


def execute_single_run(current):
    global scenario
    only_fifo = scenario.fifo
    sim = simulation.Simulation(length=scenario.length, warm_up=scenario.warm_up, stock=60,
                                high_var=scenario.high_var,
                                high_c_shortage=scenario.high_c_shortage, demands=scenario.demands,
                                distribution=scenario.distribution, L0=scenario.L0, h0=scenario.h0)
    print(current)
    print(round(((current[3] / scenario.duration) * 100), 2), "%")
    key = str(current[0]) + ", " + str(current[1]) + ", " + str(current[2])

    sim.warehouse.R = current[0]
    sim.warehouse.retailers[0].R = current[1]
    sim.warehouse.retailers[1].R = current[2]

    if not only_fifo:
        # mip
        settings.full_batches = False
        sim.run(FIFO=False)
        value_mip = create_stats(sim.collect_statistics())
        sim.reset()

        # mip - no batch splitting
        settings.full_batches = True
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
        if only_fifo:
            db[key] = (value_fifo,)
        else:
            value = group_stats((value_mip, value_batch, value_fifo))
            db[key] = value
    if parallel:
        lock.release()


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


if __name__ == '__main__':

    periods = 500
    warm_up = 10
    demands_high, distribution_high = generate_demands(periods + warm_up, True)
    demands_low, distribution_low = generate_demands(periods + warm_up, False)

    flag = False
    if flag:
        with open("demands_high.txt", "wb") as f:
            pickle.dump(demands_high, f)
        with open("demands_low.txt", "wb") as f:
            pickle.dump(demands_low, f)
    with open("demands_high.txt", "rb") as f:
        demands_high = pickle.load(f)
    with open("demands_low.txt", "rb") as f:
        demands_low = pickle.load(f)

    scenarios = []
    # block: (L0, Li) = (2,2)
    r1, r2, r3 = (15, 60), (25, 65), (25, 65)
    settings1 = {"L0": 2, "Li": 2, "high_c_shortage": True, "h0": 0.05}
    scenarios.append(sc.Scenario("DIESE, L2-2, high var, high c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings1))
    scenarios.append(sc.Scenario("DIESE L2-2, low var, high c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings1))
    settings2 = {"L0": 2, "Li": 2, "high_c_shortage": False, "h0": 0.05}
    scenarios.append(sc.Scenario("DIESE, L2-2, high var, low c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings2))
    scenarios.append(sc.Scenario("DIESE L2-2, low var, low c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings2))
 
    settings1 = {"L0": 2, "Li": 2, "high_c_shortage": True, "h0": 0.1}
    scenarios.append(sc.Scenario("DIESE, L2-2, high var, high c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings1))
    scenarios.append(sc.Scenario("DIESE L2-2, low var, high c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings1))
    settings2 = {"L0": 2, "Li": 2, "high_c_shortage": False, "h0": 0.1}
    scenarios.append(sc.Scenario("DIESE, L2-2, high var, low c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings2))
    scenarios.append(sc.Scenario("DIESE L2-2, low var, low c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings2))


    # block: (L0, Li) = (1,3)
    r1, r2, r3 = (0, 45), (25, 90), (25, 90)
    settings1 = {"L0": 1, "Li": 3, "high_c_shortage": True, "h0": 0.05}
    scenarios.append(sc.Scenario("DIESE, L1-3, high var, high c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings1))
    scenarios.append(sc.Scenario("DIESE L1-3, low var, high c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings1))
    settings2 = {"L0": 1, "Li": 3, "high_c_shortage": False, "h0": 0.05}
    scenarios.append(sc.Scenario("DIESE, L1-3, high var, low c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings2))
    scenarios.append(sc.Scenario("DIESE L1-3, low var, low c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings2))

    settings1 = {"L0": 1, "Li": 3, "high_c_shortage": True, "h0": 0.1}
    scenarios.append(sc.Scenario("DIESE, L1-3, high var, high c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings1))
    scenarios.append(sc.Scenario("DIESE L1-3, low var, high c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings1))
    settings2 = {"L0": 1, "Li": 3, "high_c_shortage": False, "h0": 0.1}
    scenarios.append(sc.Scenario("DIESE, L1-3, high var, low c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings2))
    scenarios.append(sc.Scenario("DIESE L1-3, low var, low c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings2))


    # block: (L0, Li) = (3,1)
    r1, r2, r3 = (15, 75), (10, 65), (10, 65)
    settings1 = {"L0": 3, "Li": 1, "high_c_shortage": True, "h0": 0.05}
    scenarios.append(sc.Scenario("DIESE, L3-1, high var, high c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings1))
    scenarios.append(sc.Scenario("DIESE L3-1, low var, high c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings1))
    settings2 = {"L0": 3, "Li": 1, "high_c_shortage": False, "h0": 0.05}
    scenarios.append(sc.Scenario("DIESE, L3-1, high var, low c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings2))
    scenarios.append(sc.Scenario("DIESE L3-1, low var, low c_s, low h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings2))

    settings1 = {"L0": 3, "Li": 1, "high_c_shortage": True, "h0": 0.1}
    scenarios.append(sc.Scenario("DIESE, L3-1, high var, high c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings1))
    scenarios.append(sc.Scenario("DIESE L3-1, low var, high c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings1))
    settings2 = {"L0": 3, "Li": 1, "high_c_shortage": False, "h0": 0.1}
    scenarios.append(sc.Scenario("DIESE, L3-1, high var, low c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=True, demands=demands_high,
                                 distribution=distribution_high, settings=settings2))
    scenarios.append(sc.Scenario("DIESE L3-1, low var, low c_s, high h0", periods, warm_up, r1, r2, r3, 15, 1, 1,
                                 high_var=False, demands=demands_low,
                                 distribution=distribution_low, settings=settings2))
    all_names = []
    for s in scenarios:
        all_names.append(s.name)
    with open("scenario_names.txt", "wb") as f:
        pickle.dump(all_names, f)
    for scenario in scenarios:
        before = time.time()
        run_scenario_sequential(scenario)
        after = time.time()
        db = shelve.open(scenario.name + " - header")
        observed_average = [round(sum(i) / len(i), 4) for i in scenario.demands]
        db["observed average"] = observed_average
        observed_variance = [round(variance(i, scenario.distribution[3]), 4) for i in scenario.demands]
        db["observed variance"] = observed_variance
        db["name"] = scenario.name
        db["L0"] = scenario.L0
        db["periods"] = periods
        db["warm up"] = warm_up
        db["high var"] = scenario.high_var
        db["high c ratio"] = scenario.high_c_shortage
        db["distribution"] = scenario.distribution
        db["runtime hours"] = round((after - before) / 3600, 2)
        db.close()
        print("done with scenario", scenario.name)
        reader.run(scenario.name, False)
