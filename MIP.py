# -------------------------------------------------------------------------------
# implements mathematical model underlying the MIP-based decision rules, solves the model, and returns the determined quantities to send to the retailers
# uses gurobi-API
# -------------------------------------------------------------------------------

from gurobipy import *
import settings
from combine_graphs import combine_2
from combine_graphs import transfer_to_Qs


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
        self.r = []
        self.max_orders = []
        self.q = []

    def set_params(self, warehouse, max_orders):
        self.__init__()
        self.max_orders = max_orders
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
        self.r.append(retailer.R)
        self.q.append(retailer.Q)

    def expected_invs(self, i, lead=True):

        over_est = 0    # overestimation of demand occurring per period
        x = []
        start = self.p_lead[i]
        if not lead:
            start = 0
        # todo: now its with +1 - what does it change?
        for t in range(start, self.p_lead[i] * 2 + 1):  # how many periods into future? aktuell: bei L=2 => range(2,4) => 2,3
            x.append(self.p_current_inv[i] + sum(self.p_pending_arrivals[i][:t + 1]) - (self.p_av_demand[i] + over_est) * (t + 1))

        return x

    # creates piecewise linear function for holding costs of one retailer
    def holding_objective(self, i):
        count = 0
        graph = []
        x = 0
        for x in self.expected_invs(i):

            if count == 0:
                # add initial point on x axis (-M, 0)
                graph.append((-x - 1, 0))

            # generate next point from current
            graph.append((-x, graph[-1][1] + count * (-x - graph[-1][0])))
            count += 1

        # add final point with (last_point_x + 1, last_point_y + count)
        graph.append((-x + 1, graph[-1][1] + count))

        graph_out_of_range = [g for g in graph if g[0] > self.p_stock_warehouse or g[0] > self.max_orders[i]]
        for i in range(len(graph_out_of_range) - 2):
            del graph[-1]

        return graph

    # creates piecewise linear function for shortage costs of one retailer
    def shortage_objective(self, i):

        count = 0
        graph = []
        invs = self.expected_invs(i)
        invs = [-i for i in invs if i < 0]
        invs.reverse()
        graph.append((max(invs, default=0) + 1, 0))

        for x in invs:
            graph.append((x, graph[-1][1] + count * (graph[-1][0] - x)))
            count += 1

        # insert final (first) point with x = 0, maximal y calculated as current final y in list
        graph.append((0, graph[-1][1] + count * (graph[-1][0])))
        graph.reverse()

        graph_out_of_range = [g for g in graph if g[0] > self.p_stock_warehouse or g[0] > self.max_orders[i]]
        for i in range(len(graph_out_of_range) - 1):
            del graph[-1]
        if not graph or len(graph) < 2:
            del graph[:]
            graph.append((0, 0))
            graph.append((1, 0))

        return graph

    # determines the optimal quantities to send to each retailer
    def optimal_quantities(self):

        num_i = len(self.p_lead)
        X_var = self.model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out')
        Y_fixed = self.model.addVars(num_i, vtype=GRB.BINARY, name='binary for fixed costs')

        for i in range(num_i):

            g1 = self.holding_objective(i)
            g2 = self.shortage_objective(i)
            if settings.full_batches:
                g1 = transfer_to_Qs(g1, self.q[i])
                g2 = transfer_to_Qs(g2, self.q[i])

            g_combined = combine_2(g1, self.p_c_holding[i], g2, self.p_c_shortage[i])
            if len(g_combined) == 1:
                g_combined.append((g_combined[-1][0] + 1, g_combined[-1][1]))

            list_x, list_y = map(list, zip(*g_combined))
            self.model.setPWLObj(X_var[i], list_x, list_y)
            Y_fixed[i].Obj = self.p_c_fixed_order[i]

        if settings.full_batches:
            self.model.addConstr(quicksum(X_var[i] * self.q[i] for i in X_var) <= self.p_stock_warehouse)  # ct max capacity at warehouse
            self.model.addConstrs(X_var[i] * self.q[i] <= self.max_orders[i] for i in X_var)

        else:
            self.model.addConstr(quicksum(X_var[i] for i in X_var) <= self.p_stock_warehouse)  # ct max capacity at warehouse
            self.model.addConstrs(X_var[i] <= self.max_orders[i] for i in X_var)

        self.model.addConstrs(X_var[i] <= Y_fixed[i] * self.p_stock_warehouse for i in X_var)
        self.model.optimize()

        final = [int(X_var.get(i).X) for i in range(num_i)]
        if settings.full_batches:
            final = [int(X_var.get(i).X) * self.q[i] for i in range(num_i)]

        return final
