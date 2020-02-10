import time
import sys
import numpy.random as rand
from simulation import binomial
from simulation import neg_binomial
from main_shelve import run_scenario
from main import run_scenario as run_scenario_excel


gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
import multiprocessing as mp

sys.path.append(gurobipath)
import r as rgen


scenarios = []


def split_scenario(number, length, warm_up,  high_var=False, demands=None, distribution=None):

    scenarios = []
    lb = 40
    ub = 47
    avg_num_per_s = (ub - lb + 1) / number

    lbs = []
    for i in range(number):
        lbs.append(lb + round(avg_num_per_s * i))
    for i in range(len(lbs)):
        if not i == len(lbs) - 1:
            s_ub = lbs[i + 1] - 1
        else:
            s_ub = ub
        s = rgen.R("process" + str(i), length, warm_up, (lbs[i], s_ub), (30, 60), (30, 60), 1, 40, 40, repeat=1,
                   high_c_shortage=True, high_var=high_var, run_me_as=0, demands=demands, distribution=distribution)
        scenarios.append(s)
    return scenarios


def run_parallel(length, warm_up, same_demands=False, high_var=False):
    random, distribution = None, None

    if same_demands:
        random, distribution = generate_demands(length+warm_up, high_var)
    print("Number of cpu : ", mp.cpu_count())
    pool = mp.Pool(mp.cpu_count())
    time1 = time.time()
    pool.map(run_scenario, split_scenario(mp.cpu_count(), length, warm_up, high_var=high_var, demands=random, distribution=distribution))
    print("done alle - time needed: ", time.time() - time1)
    pool.close()

def run_sequential(length, warm_up, same_demands=False, high_var=False):
    distribution = None
    random = None
    if same_demands:
        random, distribution = generate_demands(length+warm_up, high_var)

    # scenarios = split_scenario(8, length, warm_up, high_var=high_var, demands=random, distribution=distribution)
    scenarios = [rgen.R("process0 - diff", length, warm_up, (10, 50), (20, 40), (20, 40), 1, 10, 10, repeat=1,
                   high_c_shortage=True, high_var=high_var, run_me_as=2, demands=random, distribution=distribution, fifo=False)]
    for s in scenarios:
        s.number = s.number + "_seq"
        run_scenario(s)

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
    run_sequential(10100, 100, same_demands=True, high_var=True)
    # run_parallel(110, 10, same_demands=True, high_var=True)
