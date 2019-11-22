import simpy
from MIP import optimal_quantities
from MIP import update_params
import retailer
import warehouse

length = 5

warehouse = warehouse.Warehouse()
r1 = retailer.Retailer("r1", length)
r2 = retailer.Retailer("r2", length)

warehouse.add_retailer(r1)
warehouse.add_retailer(r2)

for i in range(length):
    for r in warehouse.retailers:
        r.update_inventory_morning(i)
    warehouse.print_stocks(i)

    warehouse.send_stock(i+1, 0, i)

    for r in warehouse.retailers:
        r.update_inventory_evening(i)

    warehouse.print_stocks(i)
    print("")

# loop over periods


update_params(lead=[1, 1])

print("FIRST SIM: ", optimal_quantities())

update_params(c_holding=[5, 5])

print("SECOND SIM: ", optimal_quantities())

env = simpy.Environment()
env.run(until=10)
