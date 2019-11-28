from MIP import *
import retailer as rt
import warehouse as wh
import numpy.random as rand


class Simulation:

    def __init__(self, num_retailers=2, length=100, stock=100, stochastic=True):
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock)
        for i in range(num_retailers):
            if stochastic:
                random = rand.binomial(20, 0.5, self.length)    #todo: josef: what kind of distribution? what package?
                print("retailer:", i, "rng: ", random)
            else:
                random = None
            r = rt.Retailer("retailer " + str(i), self.length, demands=random)
            self.warehouse.add_retailer(r)

    def run(self, FIFO=False):
        for i in range(self.length):
            self.warehouse.update_morning(i)
            amounts = self.amounts_requested(self.warehouse)

            if sum(amounts) > self.warehouse.stock:  # decision rule time
                if FIFO:
                    self.fifo(amounts)  # currently only works for two retailers!
                else:
                    set_params_warehouse(self.warehouse)
                    set_params_all_retailers(self.warehouse.retailers)
                    amounts = optimal_quantities()
                    print('SIMULATION! period:', i, 'stock_before:', self.warehouse.stock, 'quantities:', amounts)

            self.warehouse.send_stocks(amounts)

            self.warehouse.print_stocks(i)
            self.warehouse.update_evening()
            self.warehouse.print_stocks(i)
            print("")

    def fifo(self, amounts):  # todo: change to multiretailer implementation
        ips = []

        for r in self.warehouse.retailers:
            ips.append(r.ip())
        if ips[0] <= ips[1]:
            amounts[1] = 0
        else:
            amounts[0] = 0

        for i in range(len(amounts)):
            if amounts[i] > self.warehouse.stock:
                amounts[i] = 0

    def amount_requested(self, retailer):
        R = retailer.R
        Q = retailer.Q
        ip = retailer.ip()
        amount = 0
        while R > ip:
            amount += Q
            ip += Q
        return amount

    def amounts_requested(self, warehouse):
        a = []
        for r in warehouse.retailers:
            a.append(self.amount_requested(r))
        return a
