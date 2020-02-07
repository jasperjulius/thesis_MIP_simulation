import time
import sys
gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
import multiprocessing as mp
sys.path.append(gurobipath)

from main import scenarios
from main import run_scenario


def run_parallel():
    print("Number of cpu : ", mp.cpu_count())
    pool = mp.Pool(mp.cpu_count())
    pool.map(run_scenario, scenarios)
    print("done alle")
    pool.close()


def run_sequential():
    for s in scenarios:
        s.number = s.number+"_seq"
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

    print("rt parallel:", after1-before1)
    print("rt sequential:", after2-after1)


if __name__ == '__main__':
    time_comp()