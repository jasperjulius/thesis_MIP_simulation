from math import ceil


class Warehouse:

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
        self.b0 = []  # backorders at warehouse for retailers - of form [[number retailer, amount to ship from past order], ...] - more elaborate explanation in function get_ds
        self.doc_setup_counter = 0

    # resets warehouse to initial state; if warm_up is not None, state parameters are left out, so that the simulation can run on, but prior periods are not included in later calculation of costs
    def reset(self, warm_up=None):

        for r in self.retailers:
            r.reset(warm_up=warm_up)

        if not warm_up:
            self.stock = self.doc_stock
            self.pending_arrivals = [0, 0, 0, 0, 0, 0]
            self.b0 = []
        self.doc_inv = []  # hunt3 - fixed small bug here; was not reset after warm-up
        self.doc_setup_counter = 0

    # method for adding retailers
    def add_retailer(self, retailer):
        self.retailers.append(retailer)

        demand = sum(r.av_demand for r in self.retailers)

        self.av_demand = demand
        self.Q = sum(r.Q for r in self.retailers)

    # sends stock to warehouse from outside supplier
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
            r.doc_setup_counter += 1  # hunt3 - changed: fixed costs for sending, not ordering
        self.stock -= amount
        r.add_stock(amount, period)

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

    # returns ds, which are backorders at warehouse, organized by for which retailer they are
    #   in mip, they are always two entries, one for total backorders of rt 0, one for total backorders of rt 1 - eg: [[0, 45], [0, 30]]
    #   in fcfs, the order of backorders is important, therefore, each order has an own list elementm and the order is chronological, starting with oldest order not yet satisfied: - eg: [[1, 15],[0,30],[1,30],[0,15]]
    def get_b0(self):
        return self.b0

    # returns sum of backorders for each retailer separately - return: [int, int], eg. [20, 15]
    def sum_b0_each_retailer(self):
        result = [0, 0]
        for d in self.b0:
            result[d[0]] += d[1]
        return result

    # total sum of all backorders at warehouse - return: int, eg 45
    def sum_b0(self):
        return sum([d[1] for d in self.b0])

    # to calculate its IP, each retailer has stored backorders it has at warehouse. this method synchs backorders stored at warehouse with the retailer
    def update_b0_in_retailers(self):
        ds = self.sum_b0_each_retailer()
        for r, d in zip(self.retailers, ds):
            r.D = d

    # calculates ip of wh, comprising of stock + pending arrivals - backorders
    def ip(self):
        ip = self.stock
        ip += sum(self.pending_arrivals)
        ip -= self.sum_b0()
        return ip

    # returns q of retailer with smallest q; used as minimal possible shipment in fcfs
    def get_min_q(self):
        return min([r.Q for r in self.retailers])

    def print_stocks(self, period):
        print("period: ", period, "warehouse - stock: ", self.stock)
        for r in self.retailers:
            print(r.number, ", stock: ", r.current_inv, ", ip:", r.ip(), ", pending_arrivals: ", r.pending_arrivals)

    # determines amount ordered at supplier
    def determine_ordered_quantity(self):
        amount = max(0, ceil((self.R - (self.ip() - 1)) / self.Q)) * self.Q  # ip-1, damit bei r >= ip  bestellt wird, und nicht erst bei r>ip
        return amount
