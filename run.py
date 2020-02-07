
import sys
# gurobipath = "C:\gurobi901\win64\python37\lib\gurobipy"
import multiprocessing as mp
# sys.path.append(gurobipath)

from main import scenarios
from main import run_scenario

def run_parallel():
    pool = mp.Pool(mp.cpu_count())
    pool.map(run_scenario, scenarios)
    pool.close()

def run_sequential():
    for s in scenarios:
        run_scenario(s)

run_sequential()