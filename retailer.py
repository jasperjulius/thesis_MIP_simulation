class Retailer:

    def __init__(self, name, periods, lead=2, av_demand=10, c_holding=0.2,
                 c_shortage=5, current_inv=30,
                 c_fixed_order=1.5, R=20, Q=30):
        self.name = name
        self.lead = lead
        self.av_demand = av_demand
        self.c_holding = c_holding
        self.c_shortage = c_shortage
        self.current_inv = [current_inv]
        self.c_fixed_order = c_fixed_order
        self.pending_arrivals = [0, 0, 0, 0, 0, 0]
        self.R = R
        self.Q = Q
        self.demands = []
        for i in range(periods):
            self.demands.append(i+1)  # change to rand function later

    def update_inventory_morning(self, period):
        if period == 0:
            return

        print("updating IV - morning")
        self.current_inv.append(self.current_inv[-1] + self.pending_arrivals[period])
        self.pending_arrivals.append(0)

    def update_inventory_evening(self, period):

        print("updating IV - evening")
        self.current_inv[-1] = (self.current_inv[-1] - self.demands[period] )

    def determine_order_quantity(self):
        pass

    def add_stock(self, amount, period):
        self.pending_arrivals[self.lead + period] = amount
