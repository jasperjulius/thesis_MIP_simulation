class Warehouse:    # todo: replenishment of warehouse!

    def __init__(self, stock=100):
        self.doc_stock = stock
        self.stock = stock
        self.retailers = []
        self.pending_deliveries = [0, 0, 0, 0, 0, 0]

    def reset(self):
        for r in self.retailers:
            r.reset()
        self.stock = self.doc_stock
        self.pending_deliveries = [0, 0, 0, 0, 0, 0]

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
