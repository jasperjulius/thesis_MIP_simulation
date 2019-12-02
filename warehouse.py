from math import ceil


class Warehouse:  # todo: josef: with which rule is warehouse replenished? -> same as retailers!
    # todo: josef: costs of warehouse auch includen in total costs? gute frage
    # todo: josef: wie wähle ich die parameter (holding, shortage usw.) -> thomas arbeit

    def __init__(self, stock=100, R=60, lead=2, c_holding=0.2, c_fixed_order=2.0):
        self.av_demand = 0
        self.c_fixed_order = c_fixed_order
        self.c_holding = c_holding
        self.doc_stock = stock
        self.stock = stock
        self.R = R
        self.Q = 0
        self.lead = lead
        self.retailers = []
        self.pending_arrivals = [0, 0, 0, 0, 0, 0]

    def reset(self):
        for r in self.retailers:
            r.reset()
        self.stock = self.doc_stock
        self.pending_arrivals = [0, 0, 0, 0, 0, 0]

    # method for adding retailers
    def add_retailer(self, retailer):
        self.retailers.append(retailer)
        demand = 0
        for r in self.retailers:
            demand += r.av_demand
        self.av_demand = demand
        self.Q = ceil((2 * demand * self.c_fixed_order / self.c_holding) ** 0.5)
        pass

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

    def print_stocks(self, period):
        print("period: ", period, "warehouse - stock: ", self.stock)
        for r in self.retailers:
            print(r.name, ", stock: ", r.current_inv, ", ip:", r.ip(), ", pending_arrivals: ", r.pending_arrivals)

    def update_morning(self, period):
        for r in self.retailers:
            r.update_morning(period)

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

    def update_self(self):
        self.stock += self.pending_arrivals[0]
        self.pending_arrivals[0] = 0
        self.pending_arrivals.append(0)
        del self.pending_arrivals[:1]
        pass
