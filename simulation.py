import MIP as mip
import retailer as rt
import warehouse as wh
import numpy.random as rand
import mytimes
import time
from math import ceil


def amount_requested(retailer):
    R = retailer.R
    Q = retailer.Q
    ip = retailer.ip()
    return max(0, ceil((R - ip) / Q)) * Q


def amounts_requested(warehouse, i):
    a = []
    for r in warehouse.retailers:
        a.append(amount_requested(r))
    return a


class Simulation:

    def __init__(self, num_retailers=2, length=100, stock=100, stochastic=True, thomas=False):
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock, thomas=thomas)
        self.stats = None
        self.num_retailers = num_retailers

        for i in range(num_retailers):

            if stochastic:

                seed = rand.randint(0, 10000, 1)[0]  # todo: wieder seedfrei am ende, nur fürs testen
                rand.seed(seed)
                if not thomas:  # todo: if not thomas
                    # random = rand.negative_binomial(4, 0.4, length)
                    random = rand.negative_binomial(6, 0.6, length)
                else:
                    random = rand.poisson(2 * i + 2, length)  # todo: find out parameter
                    # todo: alternatively compound poisson

            else:
                random = None

            r = rt.Retailer(i, self.length, seed=seed, demands=random, thomas=thomas)
            self.warehouse.add_retailer(r)

    def run(self, FIFO=False, RAND=False):

        for i in range(self.length):
            # self.warehouse.print_stocks(i)
            self.warehouse.update_morning(i)
            self.warehouse.update_self()

            initial_amounts = amounts_requested(self.warehouse, i)
            ds = self.warehouse.get_ds()
            # ds = [0, 0] todo: for testing with old rule
            amounts_sent = [a + d for a, d in zip(initial_amounts, ds)]
            amounts_request = amounts_sent.copy()

            flag = False
            if sum(amounts_sent) > self.warehouse.stock:  # decision rule time
                if FIFO:  # todo: with D included in amount requested, it is not guaranteed that amount_sent is a multiple of Q
                    self.fifo(amounts_sent)  # currently only works for two retailers!
                elif RAND:
                    self.random(amounts_sent)
                else:
                    if self.warehouse.stock is not 0:
                        flag = True
                        model = mip.MIP()
                        model.set_params(self.warehouse)
                        amounts_sent = model.optimal_quantities()
                    else:
                        amounts_sent = [0 for i in range(self.num_retailers)]

                    # print('SIMULATION! period:', i, 'stock_before:', self.warehouse.stock, 'quantities:', amounts)

            self.warehouse.send_stocks(amounts_sent)
            self.warehouse.update_ds(amounts_request, amounts_sent)
            self.warehouse.update_doc_inv()
            self.warehouse.add_stock(amount_requested(self.warehouse))

            # self.warehouse.print_stocks(i)
            self.warehouse.update_evening()
            # self.warehouse.print_stocks(i)
            if flag:
                mytimes.add_interval(mip.t2 - mip.t1)
                mytimes.add_interval(mip.t3 - mip.t2)
                mytimes.add_interval(mip.t4 - mip.t3)
                mytimes.add_interval(mip.t5 - mip.t4)
            else:
                mytimes.add_interval(0)
                mytimes.add_interval(0)
                mytimes.add_interval(0)
                mytimes.add_interval(0)
            if i == 0:
                mytimes.delete_first()
            elif (i + 1) % 1000 == 0:
                mytimes.form_groups()
            mytimes.next_group()

    def collect_statistics(self):

        rt_invs = []
        rt_demands = []
        rt_pending = []
        rt_param_h = []
        rt_param_s = []
        rt_param_fixed = []
        total_h = []
        total_s = []
        total_f = []

        # kosten warehouse

        w = self.warehouse
        total_h.append(sum(w.doc_inv) * w.c_holding)
        total_s.append(0)
        count = 0
        for i in w.doc_arrivals:
            if i > 0:
                count += 1

        total_f.append(count * w.c_fixed_order)

        for r in self.warehouse.retailers:
            rt_invs.append(r.doc_inv)
            rt_demands.append(r.demands)
            rt_pending.append(r.doc_arrivals)
            rt_param_h.append(r.c_holding)
            rt_param_s.append(r.c_shortage)
            rt_param_fixed.append(r.c_fixed_order)
        for i in range(len(rt_invs)):  # entspricht anzahl retailer
            cost_h = 0
            cost_s = 0
            cost_f = 0
            for order in rt_pending[i]:
                if order > 0:
                    cost_f += rt_param_fixed[i]

            for inv, demand in zip(rt_invs[i], rt_demands[i]):  # simplifizierte version
                if inv > 0:
                    cost_h += inv
                elif inv < 0:
                    cost_s += -inv

            total_h.append(cost_h * rt_param_h[i])
            total_s.append(cost_s * rt_param_s[i])
            total_f.append(cost_f)

        self.stats = [total_h, total_s, total_f]
        return [total_h, total_s, total_f]

    def reset(self):
        self.stats = None
        self.warehouse.reset()

    def amounts_pre(self, stock, amounts):
        # reduce to first multiple of lot possible
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        for i in range(len(amounts)):
            amounts[i] = amounts[i] - ceil((amounts[i] - stock) / qs[i]) * qs[i]

    def random(self,
               amounts):  # todo: BAUSTELLE - sendet zu hohe mengen - zweck: randomly chooses one of the retailers to receive tha product
        for i in amounts:
            if i > self.warehouse.stock:
                i = 0

        number_retailers = len(self.warehouse.retailers)
        chosen = rand.randint(0, number_retailers - 1)
        for i in range(number_retailers):
            if not i == chosen:
                amounts[i] = 0

    def fifo(self, amounts):

        self.amounts_pre(self.warehouse.stock, amounts)

        def takeSecond(elem):
            return elem[1]

        ips = []
        i = 0
        stock = self.warehouse.stock

        for r in self.warehouse.retailers:
            ips.append((i, r.ip()))
            i += 1

        ips.sort(key=takeSecond)
        for num, ip in ips:
            if amounts[num] > stock:
                amounts[num] = 0
            else:
                stock -= amounts[num]

    def new_fifo(self, _ds, _amounts):

        stock = self.warehouse.stock
        send = [0, 0]
        ds = _ds.copy()
        amounts = _amounts.copy()

        self.amounts_pre(stock, ds)  # reduce each d to largest multiple of lot size q that is possible with current warehouse stock

        # assigning to the retailers, update stock
        # ...

        self.amounts_pre(stock, amounts)
        # assigning to the retailers, update stock
        # ...

        return send
