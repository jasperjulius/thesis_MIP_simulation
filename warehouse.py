from math import ceil


class Warehouse:

    def __init__(self, stock=100, R=60, lead=2, c_holding=0.1, c_fixed_order=1.5,
                 thomas=False):  # todo: params von thomas, stehen in retailer

        if thomas:
            c_fixed_order = 20
            c_holding = 1
            stock = 10
        self.thomas = thomas
        self.av_demand = 0
        self.c_fixed_order = c_fixed_order
        self.c_holding = c_holding
        self.doc_stock = stock
        self.doc_inv = []
        self.stock = stock
        self.R = R
        self.Q = 0
        self.lead = lead
        self.retailers = []
        self.pending_arrivals = [0, 0, 0, 0, 0, 0]
        self.ds = []
        self.doc_setup_counter = 0

    def reset(self, warm_up=None):

        for r in self.retailers:
            r.reset(warm_up=warm_up)

        if not warm_up:
            self.stock = self.doc_stock
            self.pending_arrivals = [0, 0, 0, 0, 0, 0]
            self.ds = []
            self.doc_inv = []
        self.doc_setup_counter = 0

    # method for adding retailers
    def add_retailer(self, retailer):
        self.retailers.append(retailer)

        demand = sum(r.av_demand for r in self.retailers)

        self.av_demand = demand
        self.Q = ceil((2 * demand * self.c_fixed_order / self.c_holding) ** 0.5)
        if self.thomas is True:
            self.Q = 12

    # method for sending to retailers
    def send_stock(self, amount, number_retailer):
        if self.stock < amount and amount > 0:
            print("WARNING: trying to send more than Warehouse has - aborting")
            return -1
        r = self.retailers[number_retailer]
        self.stock -= amount
        r.add_stock(amount)

    def send_stocks(self, amounts):
        for number, a in enumerate(amounts):
            self.send_stock(a, number)

    def update_ds(self):
        ds = self.sum_d_each_retailer()
        for r, d in zip(self.retailers, ds):
            r.D = d

    def print_stocks(self, period):
        print("period: ", period, "warehouse - stock: ", self.stock)
        for r in self.retailers:
            print(r.number, ", stock: ", r.current_inv, ", ip:", r.ip(), ", pending_arrivals: ", r.pending_arrivals)

    def get_ds(self):
        return self.ds

        # return self.ds_timebound

    def sum_d_each_retailer(self):
        result = [0, 0]
        for d in self.ds:
            result[d[0]] += d[1]
        return result

    def sum_ds(self):
        return sum([d[1] for d in self.ds])

    # sum over ds_timebound; dependent on structure of ds_timebound

    def update_morning(self, period):

        for r in self.retailers:
            r.update_morning(period)

    def update_self(self):
        self.stock += self.pending_arrivals[0]
        self.pending_arrivals[0] = 0
        self.pending_arrivals.append(0)
        del self.pending_arrivals[:1]

    def update_doc_inv(self):  # to be called after pending arrivals and orders of retailers have been processed
        self.doc_inv.append(self.stock)

    def update_evening(self):
        for r in self.retailers:
            r.update_evening()

    def ip(self):
        ip = self.stock
        for amount in self.pending_arrivals:
            ip += amount
        return ip

    def add_stock(self, amount):
        self.pending_arrivals[self.lead] = amount

    def get_min_q(self):
        return min([r.Q for r in self.retailers])
