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
    amount = max(0, ceil((R - (ip - 1)) / Q)) * Q   # ip-1, damit bei r >= ip  bestellt wird, und nicht erst bei r>ip
    return amount


def retailer_orders(warehouse, i):
    a = []
    for r in warehouse.retailers:
        a.append(amount_requested(r))
    return a


def neg_binomial(n, p):
    mu = round(n * (1 - p) / p, 3)
    var = round(n * (1 - p) / p ** 2, 3)
    return ["neg bin:", n, p, mu, var]


def binomial(n, p):
    mu = n * p
    var = n * p * (1 - p)
    return ["bin: ", n, p, mu, var]


class Simulation:

    def __init__(self, num_retailers=2, length=100, warm_up=None, stock=100, high_var=True, high_c_shortage=True, demands=None, distribution=None, L0=2):
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock, lead=L0)
        self.stats = None
        self.num_retailers = num_retailers
        self.warm_up = warm_up

        for i in range(num_retailers):
            if demands is None:
                if not high_var:
                    n = 20
                    p = 0.5
                    self.distribution = binomial(n, p)
                    random = rand.binomial(n, p, length)
                else:
                    n = 20
                    p = 2 / 3
                    self.distribution = neg_binomial(n, p)
                    random = [i for i in rand.negative_binomial(n, p, length)]
            else:
                random = demands[i]
                self.distribution = distribution

            r = rt.Retailer(i, self.warehouse, demands=random)
            if high_c_shortage:
                r.c_shortage = 4.9
            else:
                r.c_shortage = 0.9

            self.warehouse.add_retailer(r)

    def run(self, FIFO=False):

        for i in range(self.length):

            if i == self.warm_up:
                self.reset(warm_up=self.warm_up)
            self.warehouse.add_stock(amount_requested(self.warehouse))
            self.warehouse.process_arrivals()

            amounts_requested = retailer_orders(self.warehouse, i)
            ds = self.warehouse.get_ds()
            each_retailer_d = self.warehouse.sum_d_each_retailer()
            amounts_plus_backorders = [i + j for i, j in zip(each_retailer_d, amounts_requested)]

            if sum(amounts_plus_backorders) > self.warehouse.stock or (
                    FIFO and self.warehouse.sum_ds() > 0):  # decision rule time
                if self.warehouse.stock is not 0:
                    if FIFO:
                        amounts_sent = self.fifo(ds, amounts_requested, i)  # currently only works for two retailers!
                        self.warehouse.update_D_in_retailers()
                    else:
                        model = mip.MIP()
                        model.set_params(self.warehouse, amounts_plus_backorders)
                        amounts_sent = model.optimal_quantities()
                else:
                    if FIFO:
                        # call to fifo() to update ds: adds orders of retailers to list of ds
                        self.fifo(ds, amounts_requested, i)
                        self.warehouse.update_D_in_retailers()
                    amounts_sent = [0 for i in range(self.num_retailers)]

            else:
                amounts_sent = amounts_plus_backorders.copy()

            if not FIFO:
                self.update_ds_mip(amounts_requested, amounts_sent, ds)
                self.warehouse.update_D_in_retailers()

            self.warehouse.send_stocks(amounts_sent, i)  # includes fixed costs of rt
            self.warehouse.arrivals_retailers()
            self.warehouse.update_D_in_retailers()
            self.warehouse.update_evening(i)

    def collect_statistics(self):      # returns :[[H_0, H_1, H_2],[S_0, S_1, S_2],[F_0, F_1, F_2]]
        rt_invs = []
        p_cost_h = []
        p_cost_s = []
        p_cost_f = []
        total_h = []
        total_s = []
        total_f = []

        # kosten warehouse
        w = self.warehouse
        total_h.append(sum(w.doc_inv) * w.c_holding)
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
            for inv in rt_invs[i]:  # simplifizierte version ohne avInv, sondern mit IA as inventory for whole day
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

    @staticmethod
    def max_amount_possible(amount, stock, q):
        return amount - max(0, ceil((amount - stock) / q) * q)

    def fifo(self, _ds, _amounts, period):
        def takeSecond(elem):
            return elem[1]

        stock = self.warehouse.stock
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        ds = _ds  # not .copy(), bc allowed to edit ds
        amounts = _amounts.copy()

        send, stock = self.satisfy_ds(stock, ds)

        ips = []
        j = 0
        for r in self.warehouse.retailers:
            d = max(1, r.demands[max(0, period - 1)])
            R = r.R
            ip = r.ip()
            position = (j, (d - (R - ip)) / d)
            if position[1] < 0 and not period == 0:
                print("fcfs serving order - position too low - position:", position, ", ip: ", ip, "demand: ", d,
                      ", R:", R)
                print("ip components - pending arrivals: ", r.pending_arrivals, ", IN :", r.current_inv, " backlog D at warehouse:", r.D)
            ips.append(position)
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
                stock -= max_amount
        return send

    def update_ds_mip(self, _amounts_requested, _amounts_sent, ds):
        if not ds:
            ds.append([0, 0])
            ds.append([1, 0])
        amounts_requested = _amounts_requested.copy()
        amounts_sent = _amounts_sent.copy()

        for i in range(2):
            a = max(0, min(ds[i][1], amounts_sent[i]))
            ds[i][1] -= a
            amounts_sent[i] -= a

            if amounts_sent[i] < amounts_requested[i]:
                ds[i][1] += amounts_requested[i] - amounts_sent[i]


    def satisfy_ds(self, stock, ds):
        def amount(elem):
            return elem[1]

        def retailer(elem):
            return elem[0]

        def max_amount_possible(elem):
            return amount(elem) - max(0, ceil((amount(elem) - stock) / qs[retailer(elem)]) * qs[retailer(elem)])

        send = [0, 0]
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        min_qs = min(qs)
        del_counter = 0

        for i in ds:
            if stock < min_qs:
                for j in range(del_counter):
                    del ds[0]
                return send, stock

            if amount(i) <= stock:
                send[retailer(i)] += amount(i)
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
