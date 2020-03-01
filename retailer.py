from math import ceil


class Retailer:
    def __init__(self, number, warehouse, seed=None, lead=2, av_demand=10, c_holding=0.1, c_shortage=4.9,
                 current_inv=20,
                 c_fixed_order=1.0, R=40, demands=None):

        self.seed = seed
        self.warehouse = warehouse
        self.number = number
        self.lead = lead
        self.current_inv = current_inv
        self.av_demand = av_demand
        self.c_holding = c_holding
        self.c_shortage = c_shortage
        self.doc_inv = []
        self.doc_stock = current_inv  # used solely to reset current stock to initial stock after simulation before next run
        self.c_fixed_order = c_fixed_order
        self.pending_arrivals = self.construct_pending()
        self.R = R
        self.Q = ceil((2 * av_demand * c_fixed_order / c_holding) ** 0.5)
        self.doc_setup_counter = 0
        self.doc_pending_arrivals = self.construct_pending()
        self.D = 0
        self.demands = demands

    # resets retailer to initial state; if warm_up is not None, state parameters are left out, so that the simulation can run on, but prior periods are not included in later calculation of costs
    def reset(self, warm_up=None):
        if not warm_up:
            self.current_inv = self.doc_stock
            self.D = 0
            self.pending_arrivals = self.construct_pending()
            self.doc_pending_arrivals = self.construct_pending()
        self.doc_inv = []
        self.doc_setup_counter = 0

    # processes arrivals at retailer: outstanding orders in current period are added to physical inventory
    def process_arrivals(self):
        self.current_inv += self.pending_arrivals[0]
        self.pending_arrivals[0] = 0

    # records statistics of I_i, shifts pending arrivals to next period
    def update_evening(self, period):
        self.current_inv -= self.demands[period]
        self.doc_inv.append(self.current_inv)

        self.pending_arrivals.append(0)
        self.doc_pending_arrivals.append(0)
        del self.pending_arrivals[:1]

    # determines amount ordered at supplier
    def determine_ordered_quantity(self):
        amount = max(0, ceil((self.R - (self.ip() - 1)) / self.Q)) * self.Q  # ip-1, damit bei r >= ip  bestellt wird, und nicht erst bei r>ip
        return amount

    # adds stock sent from warehouse to pending arrivals
    def add_stock(self, amount, period):
        self.pending_arrivals[self.lead] = amount
        self.doc_pending_arrivals[period + self.lead] = amount

    # initializes pending deliveries
    def construct_pending(self):
        pending = [0]
        for i in range(self.lead):
            pending.append(0)
        return pending

    def ip(self):
        ip = self.current_inv
        ip += sum(self.pending_arrivals)
        return ip + self.D
