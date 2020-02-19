from math import ceil

class Retailer:
    # hunt: periods not needed
    def __init__(self, number, warehouse, seed=None, lead=2, av_demand=10, c_holding=0.1, c_shortage=4.9, current_inv=20,
                 c_fixed_order=1.0, R=40, demands=None):

        self.seed = seed
        self.warehouse = warehouse
        self.number = number
        self.lead = lead  # [0,0,0], [1,1,1], [2,2,2]     thomas, pp. 35-36
        self.current_inv = current_inv
        self.av_demand = av_demand  # [2,4]
        self.c_holding = c_holding  # [1,2,2]
        self.c_shortage = c_shortage  # [4,4], [10,10], [20,20]
        self.doc_inv = []
        self.doc_stock = current_inv    # used solely to reset current stock to initial stock after simulation before next run
        self.c_fixed_order = c_fixed_order  # [20,5,5]
        self.pending_arrivals = self.construct_pending()
        self.R = R  #
        self.Q = ceil((2 * av_demand * c_fixed_order / c_holding) ** 0.5)  #
        self.doc_setup_counter = 0
        self.doc_pending_arrivals = self.construct_pending()

        self.D = 0
        self.demands = demands

    def reset(self, warm_up=None):
        if not warm_up:
            self.current_inv = self.doc_stock
            self.D = 0
            self.pending_arrivals = self.construct_pending()
            self.doc_pending_arrivals = self.construct_pending()
        self.doc_inv = []
        self.doc_setup_counter = 0

    def process_arrivals(self):
        self.current_inv += self.pending_arrivals[0]
        self.pending_arrivals[0] = 0

    def update_evening(self, period):
        self.current_inv -= self.demands[period]
        self.doc_inv.append(self.current_inv)

        self.pending_arrivals.append(0)
        self.doc_pending_arrivals.append(0)
        del self.pending_arrivals[:1]

    def determine_order_quantity(self):  # currently done in simulation: amount_requested
        pass

    def add_stock(self, amount, period):
        self.pending_arrivals[self.lead] = amount
        self.doc_pending_arrivals[period + self.lead] = amount

    def construct_pending(self):
        pending = [0]
        for i in range(self.lead):
            pending.append(0)
        return pending

    def ip(self):
        ip = self.current_inv
        ip += sum(self.pending_arrivals)
        return ip + self.D
