import time
import sys

gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
import multiprocessing as mp

sys.path.append(gurobipath)
import r as rgen

from main import run_scenario

scenarios = []


def split_scenario(number):
    scenarios = []
    lb = 10
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
        s = rgen.R("testing purposes - parallel - "+str(i), (lbs[i], s_ub), (20, 60), (20, 60), 1, 1, 1, repeat=1,
                   high_c_shortage=True, high_var=False, run_me_as=0)
        scenarios.append(s)
    return scenarios


def run_parallel():
    print("Number of cpu : ", mp.cpu_count())
    pool = mp.Pool(mp.cpu_count())
    time1 = time.time()
    pool.map(run_scenario, split_scenario(mp.cpu_count()))
    print("done alle - time needed: ", time.time()-time1)
    pool.close()


def run_sequential():
    for s in scenarios:
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
    run_parallel()
