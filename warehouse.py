class Warehouse:

    def __init__(self, stock=100):
        self.stock = stock
        self.retailers = []
        self.pending_deliveries = [0, 0, 0, 0, 0, 0]
        pass

    # method for adding retailers
    def add_retailer(self, retailer):
        self.retailers.append(retailer)

    # method for sending to retailers
    def send_stock(self, amount, retailer):
        if self.stock < amount:
            print("WARNING: trying to send more than Warehouse has - aborting")
            return -1

        r = self.retailers[retailer]
        self.stock -= amount
        r.add_stock(amount)

    def print_stocks(self):
        print("warehouse - stock: ", self.stock)
        for r in self.retailers:
            print(r.name, ", stock: ", r.current_inv, "pending_arrivals: ", r.pending_arrivals)
