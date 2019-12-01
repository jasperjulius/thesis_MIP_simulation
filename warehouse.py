class Warehouse:  # todo: josef: with which rule is warehouse replenished?
    # todo: josef: costs of warehouse auch includen in toal costs?
    # todo: josef: wie wähle ich die parameter (holding, shortage usw.)

    def __init__(self, stock=100, R=20, Q=40, lead=2):
        self.doc_stock = stock
        self.stock = stock
        self.R = R
        self.Q = Q
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

    # method for sending to retailers
    def send_stock(self, amount, number_retailer):
        if self.stock < amount:
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
