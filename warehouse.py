class Warehouse:
    # warehouse object; variables beginning with "doc" are for documentation purposes, meaning they are used after simulation to calculate total costs or to reset the warehouse to its initial state

    def __init__(self, stock=100, R=60, lead=2, c_holding=0.1, c_fixed_order=1.5):

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
        self.ds = []  # backorders at warehouse for retailers - of form [[number retailer, amount to ship from past order], ...] - more elaborate explanation in function get_ds
        self.doc_setup_counter = 0

    # resets warehouse to initial state; if warm_up is not None, state parameters are left out, so that the simulation can run on, but prior periods are not included in later calculation of costs
    def reset(self, warm_up=None):

        for r in self.retailers:
            r.reset(warm_up=warm_up)

        if not warm_up:
            self.stock = self.doc_stock
            self.pending_arrivals = [0, 0, 0, 0, 0, 0]
            self.ds = []
        self.doc_inv = []
        self.doc_setup_counter = 0

    # method for adding retailers to warehouse; only called during setup of simulation
    def add_retailer(self, retailer):
        self.retailers.append(retailer)

        demand = sum(r.av_demand for r in self.retailers)

        self.av_demand = demand
        # from math import ceil
        # self.Q = ceil((2 * demand * self.c_fixed_order / self.c_holding) ** 0.5)    # todo: change back to sum
        self.Q = sum(r.Q for r in self.retailers)

    # send stock from outside supplier to wh
    def add_stock(self, amount):
        self.pending_arrivals[self.lead] = amount
        if amount > 0:
            self.doc_setup_counter += 1

    # send stock from wh to all rts - amounts: list, eg: [15, 0]
    def send_stocks(self, amounts, period):
        for number, a in enumerate(amounts):
            self.send_stock(a, number, period)

    # method for sending stock to a single retailer; increases fixed costs of respective rt - amount: int
    def send_stock(self, amount, number_retailer, period):
        if self.stock < amount and 0 < amount:
            raise Exception("aborting - trying to send more than Warehouse has - amount: ", amount, ", stock:",
                            self.stock)
        r = self.retailers[number_retailer]
        if amount > 0:
            r.doc_setup_counter += 1
        self.stock -= amount
        r.add_stock(amount, period)

    # returns ds, which are backorders at warehouse, organized by for which retailer they are
    #   in mip, they are always two entries, one for total backorders of rt 0, one for total backorders of rt 1 - eg: [[0, 45], [0, 30]]
    #   in fcfs, the order of backorders is important, therefore, each order has an own list elementm and the order is chronological, starting with oldest order not yet satisfied: - eg: [[1, 15],[0,30],[1,30],[0,15]]
    def get_ds(self):
        return self.ds

    # each retailer has stored backorders at warehouse for it that are yet unsatisfied for calculation of its IP. this method synchs backorders stored at warehouse with the retailer
    def update_D_in_retailers(self):
        ds = self.sum_d_each_retailer()
        for r, d in zip(self.retailers, ds):
            r.D = d

    # sum of backorders for each retailer- return: list, eg: [28, 14]
    def sum_d_each_retailer(self):
        result = [0, 0]
        for d in self.ds:
            result[d[0]] += d[1]
        return result

    # total sum of all backorders at warehouse - return: int, eg 42
    def sum_ds(self):
        return sum([d[1] for d in self.ds])

    def print_stocks(self, period):
        print("period: ", period, "warehouse - ip:", self.ip(), ", stock: ", self.stock, ", arrivals:",
              self.pending_arrivals, ", ds:", self.ds)
        for r in self.retailers:
            print(r.number, ", stock: ", r.current_inv, ", ip:", r.ip(), ", pending_arrivals: ", r.pending_arrivals)

    # processes arrivals at each retailer: outstanding orders in current period are added to physical inventory
    def arrivals_retailers(self):
        for r in self.retailers:
            r.process_arrivals()

    # processes arrivals at warehouse: outstanding orders in current period are added to physical inventory
    def process_arrivals(self):
        self.stock += self.pending_arrivals[0]
        self.pending_arrivals[0] = 0

    # records statistics of I_0, shifts pending arrivals to next period
    def update_evening(self, period):
        self.doc_inv.append(self.stock)
        self.pending_arrivals.append(0)
        del self.pending_arrivals[:1]
        for r in self.retailers:
            r.update_evening(period)

    # calculates ip of wh, comprising of stock + pending arrivals - backorders
    def ip(self):
        ip = self.stock
        for amount in self.pending_arrivals:
            ip += amount
        ip -= self.sum_ds()
        return ip

    # returns q of retailer with smallest q; used as minimal possible shipment in fcfs
    def get_min_q(self):
        return min([r.Q for r in self.retailers])
