class Retailer:

    def __init__(self, name, lead=2, av_demand=10, c_holding=0.2,
                 c_shortage=5, current_inv=[30],
                 c_fixed_order=1.5, R=20, Q=30):
        self.name = name
        self.lead = lead
        self.av_demand = av_demand
        self.c_holding = c_holding
        self.c_shortage = c_shortage
        self.current_inv = current_inv
        self.c_fixed_order = c_fixed_order
        self.pending_arrivals = [0, 0, 0, 0, 0, 0]
        self.R = R
        self.Q = Q

    def update_inventory(self, demand):
        print("updating IV")
        self.current_inv.append(self.current_inv[-1] - demand + self.pending_arrivals[0])
        self.pending_arrivals[0] = 0
        # outstanding_deliveries muss am ende des tages / am anfang des neuen eins weitergeshiftet werden

    def determine_order_quantity(self):
        pass

    def add_stock(self, amount):
        self.pending_arrivals[self.lead] = amount
