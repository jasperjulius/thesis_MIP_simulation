import MIP as mip
import retailer as rt
import warehouse as wh
import numpy.random as rand
import mytimes
import time
import settings
from math import ceil


def amount_requested(retailer):
    R = retailer.R
    Q = retailer.Q
    ip = retailer.ip()
    return max(0, ceil((R - ip) / Q)) * Q


def amounts_requested(warehouse, i):
    a = []
    for r in warehouse.retailers:
        amount = amount_requested(r)
        if amount >0:
            r.doc_setup_counter += 1    # todo: implement cost calculation in collect_statistics using counter
        a.append(amount)

    return a


class Simulation:

    def __init__(self, num_retailers=2, length=100, stock=100, stochastic=True, thomas=False):
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock, thomas=thomas)
        self.stats = None
        self.num_retailers = num_retailers

        for i in range(num_retailers):
            seed = -1
            if stochastic:

                seed = rand.randint(0, 10000, 1)[0]  # todo: wieder seedfrei am ende, nur fürs testen
                # rand.seed(seed)
                if not thomas:  # todo: if not thomas
                    distr_name = "neg bin"
                    n = 7
                    p = 0.7
                    self.distribution = (distr_name, n, p)
                    random = [i for i in rand.negative_binomial(n, p, length)]
                    # random = [max(0, int(round(i))) for i in rand.normal(10, 1, length)]    #todo: eig quatsch; ändern
                    avg = sum(random) / len(random)
                    pass
                else:
                    random = rand.poisson(2 * i + 2, length)  # todo: find out parameter
                    # todo: alternatively compound poisson

            else:
                random = rand.negative_binomial(7, 0.7, length)

            r = rt.Retailer(i, self.length, seed=seed, demands=random, thomas=thomas)
            self.warehouse.add_retailer(r)

    def run(self, FIFO=False, RAND=False):

        for i in range(self.length):
            # self.warehouse.print_stocks(i)
            self.warehouse.update_morning(i)
            self.warehouse.update_self()

            initial_amounts = amounts_requested(self.warehouse, i)
            ds = self.warehouse.get_ds()
            if settings.no_d:
                ds = []
            total_amount = sum(initial_amounts) + self.warehouse.sum_ds()
            amounts_sent = initial_amounts.copy()
            flag = False
            if total_amount > self.warehouse.stock or (FIFO and self.warehouse.sum_ds() > 0):  # decision rule time
                if FIFO:
                    amounts_sent = self.fifo(ds, initial_amounts)  # currently only works for two retailers!
                    pass
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
            self.warehouse.update_ds()
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

    def amounts_pre(self, stock, amounts):  # reduce each amount to first multiple of lot possible
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        for i in range(len(amounts)):
            amounts[i] = amounts[i] - max(0, ceil((amounts[i] - stock) / qs[i]) * qs[i])

    def amounts_sum_lower_stock(self, stock,
                                amounts):  # reduce each amount such that the total SUM is lower than stock and each multiple of lot
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        sent_so_far = 0
        for i in range(len(amounts)):
            amounts[i] = amounts[i] - ceil(max(0, amounts[i] - (stock - sent_so_far)) / qs[i]) * qs[i]
            sent_so_far += amounts[i]

    def resolve_conflict_random(self, stock, amounts):
        self.amounts_pre(stock, amounts)
        if sum(amounts) > stock:
            if amounts[0] <= stock and amounts[1] <= stock:
                amounts[rand.randint(0, 1)] = 0
            elif amounts[0] > stock and amounts[1] > stock:
                amounts[0] = 0
                amounts[1] = 0
            elif amounts[0] > stock:
                amounts[0] = 0
            elif amounts[1] > stock:
                amounts[1] = 0

    @staticmethod
    def max_amount_possible(amount, stock, q):
        return amount - max(0, ceil((amount - stock) / q) * q)

    def fifo(self, _ds, _amounts):

        def takeSecond(elem):
            return elem[1]
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        stock = self.warehouse.stock
        send = [0, 0]

        if stock == 0:  # todo: verbauen mit outer check for MIP
            return send
        ds = _ds
        amounts = _amounts.copy()

        if not settings.random:
            send, stock = self.satisfy_ds(stock, ds)
            self.amounts_pre(stock, amounts)
            if sum(amounts) == 0:
                return send

            ips = []
            j = 0
            for r in self.warehouse.retailers:
                ips.append((j, r.ip()))
                j += 1
            ips.sort(key=takeSecond)
            for retailer, ip in ips:
                if amounts[retailer] <= stock:
                    send[retailer] += amounts[retailer]
                    stock -= amounts[retailer]
                else:
                    max_amount = self.max_amount_possible(amounts[retailer], stock, qs[retailer])
                    send[retailer] += max_amount
                    ds.append([retailer, amounts[retailer] - max_amount])

        else:
            self.resolve_conflict_random(stock, ds)
            for num, i in enumerate(ds):
                send[num] += i
                stock -= i
            self.resolve_conflict_random(stock, amounts)
            for i, amount in enumerate(amounts):
                send[i] += amount
                stock -= amount


        return send

    def satisfy_ds(self, stock, ds):
        send = [0, 0]
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        min_qs = min(qs)
        del_counter = 0

        def amount(elem):
            return elem[1]

        def retailer(elem):
            return elem[0]

        def add(elem):
            send[retailer(elem)] += amount(elem)

        def max_amount_possible(elem):
            return amount(elem) - max(0, ceil((amount(elem) - stock) / qs[retailer(elem)]) * qs[retailer(elem)])

        for i in ds:
            if stock < min_qs:
                for j in range(del_counter):
                    del ds[0]
                return send, stock

            if amount(i) <= stock:
                add(i)
                stock -= amount(i)
                del_counter += 1
            else:
                last_shipment = max_amount_possible(i)
                send[retailer(i)] += last_shipment
                i[1] -= last_shipment
                stock -= last_shipment
        for j in range(del_counter):
            del ds[0]
        return send, stock
