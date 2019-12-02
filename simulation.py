import MIP as mip
import retailer as rt
import warehouse as wh
import numpy.random as rand
import time


class Simulation:

    def __init__(self, num_retailers=2, length=100, stock=100, stochastic=True):
        self.times = []
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock)
        self.stats = None
        self.num_retailers = num_retailers
        for i in range(num_retailers):
            if stochastic:
                random = rand.binomial(20, 0.5,
                                       self.length)  # todo: josef: what kind of distribution? what package? poisson/ neg binomial

            else:
                random = None
            r = rt.Retailer("retailer " + str(i), self.length, demands=random)
            self.warehouse.add_retailer(r)

    def collect_statistics(self):
        rt_invs = []
        rt_demands = []
        rt_param_h = []
        rt_param_s = []
        total_h = []
        total_s = []

        for r in self.warehouse.retailers:
            rt_invs.append(r.doc_inv)
            rt_demands.append(r.demands)
            rt_param_h.append(r.c_holding)
            rt_param_s.append(r.c_shortage)

        for i in range(len(rt_invs)):
            cost_h = 0
            cost_s = 0
            for inv, demand in zip(rt_invs[i], rt_demands[i]):
                if inv >= demand:
                    cost_h += inv - 0.5 * demand
                elif inv > 0:
                    cost_h += float(inv) / 2 * float(inv) / demand
                    cost_s += demand - inv
                elif inv <= 0:
                    cost_s += demand
            total_h.append(cost_h * rt_param_h[i])
            total_s.append(cost_s * rt_param_s[i])
            self.stats = [total_h, total_s]
        return self.stats

    def reset(self):
        self.stats = None
        self.warehouse.reset()

    def run(self, FIFO=False):
        for i in range(self.length):
            # self.warehouse.print_stocks(i)
            self.warehouse.update_morning(i)
            self.warehouse.update_self()

            amounts = self.amounts_requested(self.warehouse)

            if sum(amounts) > self.warehouse.stock:  # decision rule time
                if FIFO:
                    self.fifo(amounts)  # currently only works for two retailers!
                else:
                    time_before = time.time()

                    if self.warehouse.stock is not 0:
                        model = mip.MIP(self.times)
                        model.set_params_warehouse(self.warehouse)
                        model.set_params_all_retailers(self.warehouse.retailers)
                        amounts = model.optimal_quantities()
                    else:
                        amounts = [0 for i in range(self.num_retailers)]
                    self.times.append((time.time() - time_before,))

                    # print('SIMULATION! period:', i, 'stock_before:', self.warehouse.stock, 'quantities:', amounts)

            self.warehouse.send_stocks(amounts)

            self.warehouse.add_stock(self.amount_requested(self.warehouse))

            # self.warehouse.print_stocks(i)
            self.warehouse.update_evening()
            # self.warehouse.print_stocks(i)

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
