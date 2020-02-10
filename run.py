import time
import sys
import numpy.random as rand
from simulation import binomial
from simulation import neg_binomial

gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
import multiprocessing as mp

sys.path.append(gurobipath)
import r as rgen

from main import run_scenario

scenarios = []


def split_scenario(number, length, warm_up,  high_var=False, demands=None, distribution=None):

    scenarios = []
    lb = 20
    ub = 60
    avg_num_per_s = (ub - lb + 1) / number

    lbs = []
    for i in range(number):
        lbs.append(lb + round(avg_num_per_s * i))
    for i in range(len(lbs)):
        if not i == len(lbs) - 1:
            s_ub = lbs[i + 1] - 1
        else:
            s_ub = ub
        s = rgen.R("testing purposes - parallel - " + str(i), length, warm_up, (lbs[i], s_ub), (36, 60), (57, 60), 1, 5, 5, repeat=1,
                   high_c_shortage=True, high_var=high_var, run_me_as=0, demands=demands, distribution=distribution)
        scenarios.append(s)
    return scenarios


def run_parallel():
    print("Number of cpu : ", mp.cpu_count())
    pool = mp.Pool(mp.cpu_count())
    time1 = time.time()
    pool.map(run_scenario, split_scenario(mp.cpu_count()))
    print("done alle - time needed: ", time.time() - time1)
    pool.close()

# todo: run_sequential works with injecting list of demands. same for run_parallel
def run_sequential(length, warm_up, same_demands=False, high_var=False):
    distribution = None
    random = None
    if same_demands:
        if not high_var:
            n = 20
            p = 0.5
            distribution = binomial(n, p)
            random = rand.binomial(n, p, length)
        else:
            n = 20
            p = 2 / 3
            distribution = neg_binomial(n, p)
            random = [i for i in rand.negative_binomial(n, p, length)]

    for s in split_scenario(8, length, warm_up, high_var=high_var, demands=random, distribution=distribution):
        s.number = s.number + "_seq"
        run_scenario(s)


def time_test(s):
    print("beginning waiting")
    time.sleep(4)
    print("done")


def time_comp():
    before1 = time.time()
    run_parallel()
    after1 = time.time()
    run_sequential()
    after2 = time.time()

    print("rt parallel:", after1 - before1)
    print("rt sequential:", after2 - after1)


if __name__ == '__main__':
    run_sequential(10100, 100, same_demands=True)
