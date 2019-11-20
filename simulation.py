import simpy
from model_piecewise_one_func import optimal_quantities
from model_piecewise_one_func import update_params

update_params(lead=[1,1])

print("FIRST SIM: ", optimal_quantities())

update_params(c_holding=[5,5])

print("SECOND SIM: ", optimal_quantities())

env = simpy.Environment()
env.run(until=10)

