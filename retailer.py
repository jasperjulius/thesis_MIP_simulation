class Retailer:

    def __init__(self, name, periods, lead=2, av_demand=10, c_holding=0.2,
                 c_shortage=50, current_inv=30,
                 c_fixed_order=0.1, R=40, Q=20, demands=None):
        self.name = name
        self.lead = lead
        self.av_demand = av_demand
        self.c_holding = c_holding
        self.c_shortage = c_shortage
        self.doc_inv = []  # every period's inventory after arrivals, before demand
        self.current_inv = current_inv
        self.c_fixed_order = c_fixed_order
        self.pending_arrivals = self.construct_pending()
        self.doc_arrivals = self.construct_pending()
        self.R = R
        self.Q = Q
        self.demands = []
        self.period = 0
        if demands is None:
            for i in range(periods):
                self.demands.append(
                    self.av_demand)
        else:
            self.demands = demands

    def reset(self):
        self.current_inv = self.doc_inv[0]
        self.doc_inv = []

        self.pending_arrivals = self.construct_pending()
        self.doc_arrivals = self.construct_pending()

    def update_morning(self, period):
        self.period = period

        self.doc_inv.append(self.current_inv + self.pending_arrivals[0])
        self.current_inv += self.pending_arrivals[0]
        self.doc_arrivals[period] = self.pending_arrivals[0]
        self.pending_arrivals[0] = 0
        self.doc_arrivals.append(0)

    def update_evening(self):

        self.pending_arrivals.append(0)
        self.pending_arrivals = self.pending_arrivals[1:]
        self.current_inv -= self.demands[self.period]

    def determine_order_quantity(self):  # currently done in simulation: amount_requested
        pass

    def add_stock(self, amount):
        self.pending_arrivals[self.lead] = amount

    def ip(self):
        ip = self.current_inv
        for amount in self.pending_arrivals:
            ip += amount
        return ip

    def construct_pending(self):
        pending = [0]
        for i in range(self.lead):
            pending.append(0)
        return pending

