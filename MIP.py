from gurobipy import *
import mytimes


class MIP:

    def __init__(self):
        self.model = Model()
        self.model.setParam('OutputFlag', False)
        self.p_stock_warehouse = None
        self.p_lead = []
        self.p_av_demand = []
        self.p_c_holding = []
        self.p_c_shortage = []
        self.p_c_fixed_order = []
        self.p_current_inv = []
        self.p_pending_arrivals = []
        self.ips = []

    def set_params(self, warehouse):
        self.__init__()
        if warehouse.stock > 0:
            self.p_stock_warehouse = warehouse.stock
        else:
            self.p_stock_warehouse = 0

        for r in warehouse.retailers:
            self.set_params_retailer(r)

    def set_params_retailer(self, retailer):
        self.p_lead.append(retailer.lead)
        self.p_av_demand.append(retailer.av_demand)
        self.p_c_holding.append(retailer.c_holding)
        self.p_c_shortage.append(retailer.c_shortage)
        self.p_current_inv.append(retailer.current_inv)
        self.p_c_fixed_order.append(retailer.c_fixed_order)
        self.p_pending_arrivals.append(retailer.pending_arrivals)
        self.ips.append(retailer.ip())

    def expected_invs(self, i, lead=True):
        x = []
        start = self.p_lead[i]
        if not lead:
            start = 0
        for t in range(start,
                       self.p_lead[i] * 2):  # how many periods into future? aktuell: bei L=2 => range(2,4) => 2,3

            x.append(self.p_current_inv[i] + sum(self.p_pending_arrivals[i][:t + 1]) - self.p_av_demand[i] * t)
        return x





    def holding_objective(self, X_holding,
                          i):  # average inventory of retailer i in period t - only for t >= leadtime
        count = 0
        graph = []
        x = 0

        for t in range(self.p_lead[i],
                       self.p_lead[i] * 2):  # how many periods into future? aktuell: bei L=2 => range(2,4) => 2,3

            x = self.p_current_inv[i] + sum(self.p_pending_arrivals[i][:t + 1]) - self.p_av_demand[
                i] * t  # nimmt inventory am anfang der periode (höhster punkt)

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

    def shortage_objective(self, X_shortage, i):

        count = 0
        graph = []
        x = self.expected_invs(i)
        x = [-i for i in x if i < 0]
        x.reverse()
        graph.append((max(x, default=0) + 1, 0))

        for current in x:
            graph.append((current, graph[-1][1] + count * (graph[-1][0] - current)))
            count += 1

        # insert final (first) point with x = 0, maximal y calculated as current final y in list + count (+1?)
        graph.append((0, graph[-1][1] + count * (graph[-1][0])))
        graph.reverse()
        list_x, list_y = map(list, zip(*graph))

        self.model.setPWLObj(X_shortage[i], list_x, list_y)

    # erster wert jeweils für t = 0, also "jetzt"; aktuell wird so gerechnet, als kämen deliveries first thing in the morning an, und sind somit im täglichen inventory zur berechnung der holding/shortage costs mit drin

    def order_setup_objective(self, X_order_setup, i):

        x = self.expected_invs(i, lead=False)
        ip = self.ips[i]
        av_demand = self.p_av_demand[i]
        graph = []



    def optimal_quantities(self):

        # all time results based on 400 periods, if not stated otherwise!
        # var block: no up, avg: 0.0004
        num_i = len(self.p_lead)
        X_holding = self.model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out - holding')
        X_shortage = self.model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out - shortage (helper var) ')
        X_order_setup = self.model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out - order setup (helper var) ')
        X_fixed = self.model.addVars(num_i, vtype=GRB.BINARY,
                                     name='binary delivering to i')  # wird ersetzt durch neuen constraint?

        for i in range(num_i):
            # trend up!!! avg first 40: 0.0005 , last 40: 0.008 (~factor 16)
            self.holding_objective(X_holding, i)

            # no up, avg: 0.00003
            self.shortage_objective(X_shortage, i)

            self.order_setup_objective(X_order_setup, i)

            # no up, avg: 0.000008
            X_fixed[i].Obj = self.p_c_fixed_order[i]

        # ct block: no up, avg: 0.0002
        self.model.addConstr(
            quicksum(X_holding[i] for i in X_holding) <= self.p_stock_warehouse)  # ct max capacity at warehouse
        self.model.addConstrs(X_holding[i] == X_shortage[i] for i in X_holding)  # ct(i) hilfsvariable constraint
        self.model.addConstrs(X_holding[i] == X_order_setup[i] for i in X_holding)  # ct(i) hilfsvariable constraint
        self.model.addConstrs(
            X_holding[i] <= X_fixed[i] * self.p_stock_warehouse for i in X_holding)  # ct fixed order costs

        self.model.optimize()  # no up, avg: 0.0009

        # model.printAttr('x')
        final = []
        for i in range(num_i):
            final.append(int(X_holding.get(i).X))
        return final





    def holding_objective_alt(self, X_holding,
                              i):  # average inventory of retailer i in period t - only for t >= leadtime

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

    @staticmethod
    def average(stock, demand):
        if stock >= demand:
            return stock - 0.5 * demand
        elif stock > 0:
            return float(stock) / 2 * float(stock) / demand
        elif stock <= 0:
            return 0
