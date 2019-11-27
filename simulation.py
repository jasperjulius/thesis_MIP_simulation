from MIP import *
import retailer as rt
import warehouse as wh


def amounts_requested(warehouse, period):
    a = []
    for r in warehouse.retailers:
        a.append(amount_requested(r, period))
    return a


def amount_requested(retailer, period):
    R = retailer.R
    Q = retailer.Q
    ip = retailer.ip()
    amount = 0
    while R > ip:
        amount += Q
        ip += Q
    return amount


length = 11

warehouse = wh.Warehouse(stock=205)

warehouse.add_retailer(rt.Retailer("r1", length))
warehouse.add_retailer(rt.Retailer("r2", length))

for i in range(length):

    warehouse.update_morning(i)

    amounts = amounts_requested(warehouse, i)

    if sum(amounts) > warehouse.stock:  # decision rule time
        set_params_warehouse(warehouse)
        set_params_all_retailers(warehouse.retailers)

        amounts = optimal_quantities()
        print('SIMULATION! period:', i, 'stock_before:', warehouse.stock, 'quantities:', amounts)

    warehouse.send_stocks(amounts)

    warehouse.print_stocks(i)
    warehouse.update_evening()
    warehouse.print_stocks(i)
    print("")
