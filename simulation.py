import simpy
from MIP import optimal_quantities
from MIP import update_params
import retailer
import warehouse

length = 100

warehouse = warehouse.Warehouse()
r1 = retailer.Retailer("r1")
r2 = retailer.Retailer("r2")

warehouse.add_retailer(r1)
warehouse.add_retailer(r2)

warehouse.print_stocks()

warehouse.send_stock(20, 0)

warehouse.print_stocks()

# need to generate list of stochastic demands
# loop over periods



update_params(lead=[1, 1])

print("FIRST SIM: ", optimal_quantities())

update_params(c_holding=[5, 5])

print("SECOND SIM: ", optimal_quantities())

env = simpy.Environment()
env.run(until=10)
