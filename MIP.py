from gurobipy import *
import time


class MIP:

    def __init__(self, times):
        self.times = times
        self.model = Model()
        self.model.setParam('OutputFlag', False)
        self.p_stock_warehouse = None
        self.p_lead = []
        self.p_av_demand = []
        self.p_c_holding = []
        self.p_c_shortage = []
        self.p_current_inv = []
        self.p_c_fixed_order = []

    def average(self, stock, demand):
        if stock >= demand:
            return stock - 0.5 * demand
        elif stock > 0:
            return float(stock) / 2 * float(stock) / demand
        elif stock <= 0:
            return 0

    def holding_objective_old(self, X_holding,
                              i):  # average inventory of retailer i in period t - only for t >= leadtime
        count = 0
        graph = []
        x = 0

        for t in range(self.p_lead[i], self.p_lead[i] * 2 + 1):  # how many periods into future?

            x = self.p_current_inv[i] + sum(self.p_pending_arrivals[i][:t + 1]) - self.p_av_demand[i] * (t + 0.5)

            if count == 0:
                # add initial point on x axis (-M, 0)
                graph.append((-x - 1, 0))

            # generate next point from current
            graph.append((-x, graph[-1][1] + count * (-x - graph[-1][0])))
            count += 1

        # add final point with  (last_point_x + 1, last_point_y + count)
        graph.append((-x + 1, graph[-1][1] + count))

        # transform tuples into two lists
        list_x, list_y = map(list, zip(*graph))

        # scale graph according to holding costs of i
        list_y = [j * self.p_c_holding[i] for j in list_y]

        # add curve as one connected, but not continuous obj function for variable X[i]
        self.model.setPWLObj(X_holding[i], list_x, list_y)
        return

    def holding_objective(self, X_holding, i):  # average inventory of retailer i in period t - only for t >= leadtime

        # no up, avg: 0.000008
        graph = []
        stocks = []
        for t in range(self.p_lead[i], self.p_lead[i] * 2 + 1):  # how many periods into future?
            stocks.append(self.p_current_inv[i] + sum(self.p_pending_arrivals[i][:t + 1]) - self.p_av_demand[i] * t)


        upper_bound = -1 * (stocks[-1] - self.p_av_demand[i]) + 1
        if upper_bound > self.p_stock_warehouse >= 0:
            upper_bound = self.p_stock_warehouse
        if upper_bound <= 0:
            upper_bound = 1

        for x in range(upper_bound + 1):
            av_stock = 0
            for stock in stocks:  # calculate average stock of each period
                av_stock += self.average(stock + x, self.p_av_demand[i])
            graph.append((x, av_stock))

        # transform tuples into two lists
        list_x, list_y = map(list, zip(*graph))

        # scale graph according to holding costs of i
        list_y = [j * self.p_c_holding[i] for j in list_y]

        # add curve as one connected, but not continuous obj function for variable X[i]
        self.model.setPWLObj(X_holding[i], list_x, list_y)
        return

    def shortage_objective(self, X_shortage, i):
        ip = []
        missed_deliveries = []
        total_loss = 0
        sum_missed_deliveries = 0

        for t in range(self.p_lead[i], self.p_lead[i] * 2 + 2):
            ip.append(self.p_current_inv[i] + sum(self.p_pending_arrivals[i][:t + 1]) - self.p_av_demand[i] * t)

        for j in range(1, len(ip)):
            loss = 0

            if ip[j - 1] >= 0 and ip[j] >= 0:
                loss = 0
            if ip[j - 1] >= 0 > ip[j]:
                loss = -ip[j]
            if ip[j - 1] < 0 and ip[j] < 0:
                loss = ip[j - 1] - ip[j]

            missed_deliveries.append(loss)
            sum_missed_deliveries = sum(missed_deliveries)
            total_loss = sum_missed_deliveries * self.p_c_shortage[i]

        graph = [(0, total_loss), (sum_missed_deliveries, 0), (sum_missed_deliveries + 1, 0)]
        list_x, list_y = map(list, zip(*graph))

        self.model.setPWLObj(X_shortage[i], list_x, list_y)

    # erster wert jeweils für t = 0, also "jetzt"; aktuell wird so gerechnet, als kämen deliveries first thing in the morning an, und sind somit im täglichen inventory zur berechnung der holding/shortage costs mit drin
    p_pending_arrivals = []

    def set_params_warehouse(self, warehouse):
        if warehouse.stock > 0:
            self.p_stock_warehouse = warehouse.stock
        else:
            self.p_stock_warehouse = 0

    def set_params_all_retailers(self, retailers):

        self.p_lead = []
        self.p_av_demand = []
        self.p_c_holding = []
        self.p_c_shortage = []
        self.p_current_inv = []
        self.p_c_fixed_order = []
        self.p_pending_arrivals = []

        for r in retailers:
            self.set_params_retailer(r)

    def set_params_retailer(self, retailer):
        self.p_lead.append(retailer.lead)
        self.p_av_demand.append(retailer.av_demand)
        self.p_c_holding.append(retailer.c_holding)
        self.p_c_shortage.append(retailer.c_shortage)
        self.p_current_inv.append(retailer.current_inv)
        self.p_c_fixed_order.append(retailer.c_fixed_order)
        self.p_pending_arrivals.append(retailer.pending_arrivals)

    def update_params(self, stock_warehouse=None, lead=None, av_demand=None, c_holding=None, c_shortage=None,
                      current_inv=None,
                      c_fixed_order=None, outstanding_deliveries=None):

        if stock_warehouse is not None:
            self.p_stock_warehouse = stock_warehouse

        if lead is not None:
            self.p_lead = lead

        if av_demand is not None:
            self.p_av_demand = av_demand

        if c_holding is not None:
            self.p_c_holding = c_holding

        if c_shortage is not None:
            self.p_c_shortage = c_shortage

        if current_inv is not None:
            self.p_current_inv = current_inv

        if c_fixed_order is not None:
            self.p_c_fixed_order = c_fixed_order

        if outstanding_deliveries is not None:
            self.p_pending_arrivals = outstanding_deliveries

    def optimal_quantities(self):

        # all time results based on 400 periods, if not stated otherwise!
        # var block: no up, avg: 0.0004
        num_i = len(self.p_lead)
        X_holding = self.model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out - holding')
        X_shortage = self.model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out - shortage (helper var) ')
        X_fixed = self.model.addVars(num_i, vtype=GRB.BINARY, name='binary delivering to i')

        for i in range(num_i):

            # trend up!!! avg first 40: 0.0005 , last 40: 0.008 (~factor 16)
            self.holding_objective(X_holding, i)

            # no up, avg: 0.00003
            self.shortage_objective(X_shortage, i)

            # no up, avg: 0.000008
            X_fixed[i].Obj = self.p_c_fixed_order[i]

        # ct block: no up, avg: 0.0002
        self.model.addConstr(
            quicksum(X_holding[i] for i in X_holding) <= self.p_stock_warehouse)  # ct max capacity at warehouse
        self.model.addConstrs(X_holding[i] == X_shortage[i] for i in X_holding)  # ct(i) hilfsvariable constraint
        self.model.addConstrs(X_holding[i] <= X_fixed[i] * self.p_stock_warehouse for i in X_holding)  # ct fixed order costs

        self.model.optimize()   # no up, avg: 0.0009


        # model.printAttr('x')
        final = []
        for i in range(num_i):
            final.append(int(X_holding.get(i).X))
        return final
