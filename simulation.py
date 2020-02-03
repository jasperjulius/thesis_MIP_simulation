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
    amount = max(0, ceil((R - ip) / Q)) * Q
    if amount > 0:
        retailer.doc_setup_counter += 1
    return amount


def amounts_requested(warehouse, i):
    a = []
    for r in warehouse.retailers:
        a.append(amount_requested(r))
    return a


def neg_binomial(n, p):
    mu = n * (1 - p) / p
    var = n * (1 - p) / p ** 2
    return ["neg bin:", n, p, mu, var]


def binomial(n, p):
    mu = n * p
    var = n * p * (1 - p)
    return ["bin: ", n, p, mu, var]


class Simulation:

    def __init__(self, num_retailers=2, length=100, warm_up=None, stock=100, high_var=True, high_c_shortage=True):
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock)
        self.stats = None
        self.num_retailers = num_retailers
        self.warm_up = warm_up

        for i in range(num_retailers):
            seed = rand.randint(0, 10000, 1)[0]
            # rand.seed(seed)
            if not high_var:
                n = 20
                p = 0.5
                self.distribution = binomial(n, p)
                random = rand.binomial(n, p, length)
                # random = [max(0, int(round(i))) for i in rand.normal(10, 0, length)]    #todo: tryen mit höheren Rs, einfach interesse; params richtig labeln
            else:
                n = 20
                p = 2 / 3
                self.distribution = neg_binomial(n, p)
                random = [i for i in rand.negative_binomial(n, p, length)]
            avg = sum(random) / len(random)

            r = rt.Retailer(i, self.length, seed=seed, demands=random)
            if high_c_shortage:
                r.c_shortage = 4.9
            else:
                r.c_shortage = 0.9

            self.warehouse.add_retailer(r)

    def run(self, FIFO=False):

        for i in range(self.length):

            if i == self.warm_up:
                self.reset(warm_up=self.warm_up)
            self.warehouse.update_morning(i)
            self.warehouse.update_self()

            initial_amounts = amounts_requested(self.warehouse, i)
            ds = self.warehouse.get_ds()
            each_retailer_d = self.warehouse.sum_d_each_retailer()
            total_orders = [i + j for i, j in zip(each_retailer_d, initial_amounts)]
            total_amount = sum(initial_amounts) + sum(each_retailer_d)
            amounts_sent = initial_amounts.copy()
            flag = False

            if total_amount > self.warehouse.stock or (FIFO and self.warehouse.sum_ds() > 0) or settings.ignore:  # decision rule time
                if self.warehouse.stock is not 0:
                    if FIFO:
                        amounts_sent = self.fifo(ds, initial_amounts, i)  # currently only works for two retailers!
                    else:

                        flag = True
                        model = mip.MIP()
                        model.set_params(self.warehouse, total_orders)
                        amounts_sent = model.optimal_quantities()
                        self.update_ds_mip(initial_amounts, amounts_sent, ds)

                else:
                    amounts_sent = [0 for i in range(self.num_retailers)]

            self.warehouse.send_stocks(amounts_sent)
            self.warehouse.update_ds()
            self.warehouse.update_doc_inv()
            self.warehouse.add_stock(amount_requested(self.warehouse))
            self.warehouse.update_evening()

            if flag:
                mytimes.add_interval(mip.t2 - mip.t1)
                mytimes.add_interval(mip.t3 - mip.t2 + mip.t5 - mip.t4)
                mytimes.add_interval(mip.t4 - mip.t3 + mip.t6 - mip.t5)
                mytimes.add_interval(mip.t7 - mip.t6)
                mytimes.add_interval(mip.t8 - mip.t7)
            else:
                mytimes.add_interval(0)
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
        p_cost_h = []
        p_cost_s = []
        p_cost_f = []
        total_h = []
        total_s = []
        total_f = []

        # kosten warehouse
        w = self.warehouse
        total_h.append(sum(w.doc_inv[self.warm_up:]) * w.c_holding)
        total_s.append(0)
        total_f.append(w.doc_setup_counter * w.c_fixed_order)

        # kosten retailers
        for r in self.warehouse.retailers:
            rt_invs.append(r.doc_inv)
            p_cost_h.append(r.c_holding)
            p_cost_s.append(r.c_shortage)
            p_cost_f.append(r.c_fixed_order)

        for i in range(len(rt_invs)):  # entspricht anzahl retailer
            cost_h = 0
            cost_s = 0

            # order setup costs calculation
            cost_f = w.retailers[i].doc_setup_counter * p_cost_f[i]
            total_f.append(cost_f)

            # holding, shortage costs calculation
            for inv in rt_invs[i][
                       self.warm_up:]:  # simplifizierte version ohne avInv, sondern mit IA as inventory for whole day
                if inv > 0:
                    cost_h += inv
                elif inv < 0:
                    cost_s += -inv

            total_h.append(cost_h * p_cost_h[i])
            total_s.append(cost_s * p_cost_s[i])

        self.stats = [total_h, total_s, total_f]
        return [total_h, total_s, total_f]

    def reset(self, warm_up=None):
        self.stats = None
        self.warehouse.reset(warm_up=warm_up)

    def amounts_pre(self, stock, amounts):  # reduce each amount to first multiple of lot possible
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        for i in range(len(amounts)):
            amounts[i] = amounts[i] - max(0, ceil((amounts[i] - stock) / qs[i]) * qs[i])

    @staticmethod
    def max_amount_possible(amount, stock, q):
        return amount - max(0, ceil((amount - stock) / q) * q)

    def fifo(self, _ds, _amounts, period):
        def takeSecond(elem):
            return elem[1]

        stock = self.warehouse.stock
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        ds = _ds
        amounts = _amounts.copy()

        send, stock = self.satisfy_ds(stock, ds)
        self.amounts_pre(stock, amounts)
        if sum(amounts) == 0:
            return send

        ips = []
        j = 0
        for r in self.warehouse.retailers:  # todo: das muss nochmal überdacht werden...
            d = min(1, r.demands[min(0, period - 1)])
            R = r.R
            ip = r.ip()
            ips.append((j, (d - (R - ip)) / d))
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

        return send

    def update_ds_mip(self, _amounts_requested, _amounts_sent, ds):  # todo: ds initialization where?
        if not ds:
            ds.append([0, 0])
            ds.append([1, 0])
        amounts_requested = _amounts_requested.copy()
        amounts_sent = _amounts_sent.copy()

        def reduce_by(a1, a2):
            return max(0, min(a1, a2))

        for i in range(2):

            a = reduce_by(ds[i][1], amounts_sent[i])
            ds[i][1] -= a
            amounts_sent[i] -= a

            if amounts_sent[i] < amounts_requested[i]:
                ds[i][1] += amounts_requested[i] - amounts_sent[i]

            # erriting okay, set ds to zero, create new ds with difference amount_left_after_satisfying_ds, initial_order
            # not enuf, reduce ds as far as possible,

        # satisfy outstanding orders, add

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
