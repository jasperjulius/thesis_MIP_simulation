import simpy
from gurobipy import *


# TODO: aktuell wird mit dem tagesmittelwert gerechnet. dies ist eine akkurate angabe bei positivem inventory an morgen und abend, aber nicht bei wechsel von pos auf neg. (iv/2*iv/d)
def holding_piecewise_objectives(i):  # average inventory of retailer i in period t - only for t >= leadtime
    count = 0
    graph = []
    x = 0

    for t in range(p_lead[i], p_lead[i] * 2 + 1):  # how many periods into future?

        x = p_current_inv[i] + sum(p_outstanding_deliveries[i][:t + 1]) - p_av_demand[i] * (t + 0.5)

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
    list_y = [j * p_c_holding[i] for j in list_y]

    # add curve as one connected, but not continuous obj function for variable X[i]
    model.setPWLObj(X_holding[i], list_x, list_y)
    return


def shortage_objective(i):
    ip = []
    missed_deliveries = []
    total_loss = 0
    sum_missed_deliveries = 0

    for t in range(p_lead[i], p_lead[i] * 2 + 2):
        ip.append(p_current_inv[i] + sum(p_outstanding_deliveries[i][:t + 1]) - p_av_demand[i] * t)

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
        total_loss = sum_missed_deliveries * p_c_shortage[i]

    graph = [(0, total_loss), (sum_missed_deliveries, 0), (sum_missed_deliveries + 1, 0)]
    list_x, list_y = map(list, zip(*graph))

    model.setPWLObj(X_shortage[i], list_x, list_y)


# MODEL
num_i = 2
model = Model()
model.setParam( 'OutputFlag', False )
X_holding = model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out')
X_shortage = model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out (helper var) ')
X_fixed = model.addVars(num_i, vtype=GRB.BINARY, name='delivering to i')

p_stock_warehouse = 200

p_lead = [2, 2]
p_av_demand = [10, 10]
p_c_holding = [0.3, 0.3]
p_c_shortage = [3, 3]
p_current_inv = [40, 10]
p_c_fixed_order = [3.90, 3.90]


# erster wert jeweils für t = 0, also "jetzt"; aktuell wird so gerechnet, als kämen deliveries first thing in the morning an, und sind somit im täglichen inventory zur berechnung der holding/shortage costs mit drin
p_outstanding_deliveries = [[2, 2, 2, 2, 2],
                            [2, 2, 2, 2, 2]]

access_all = [p_lead, p_av_demand, p_c_holding, p_c_shortage, p_current_inv, p_c_fixed_order, p_outstanding_deliveries]
for i in range(2, num_i):
    for j in access_all:
        j.append(j[-2])


def update_params(stock_warehouse=None, lead=None, av_demand=None, c_holding=None, c_shortage=None, current_inv=None, c_fixed_order=None, outstanding_deliveries=None):

    global p_stock_warehouse
    global p_lead
    global p_av_demand
    global p_c_holding
    global p_c_shortage
    global p_current_inv
    global p_c_fixed_order
    global p_outstanding_deliveries

    if not stock_warehouse is None:
        p_stock_warehouse = stock_warehouse

    if not lead is None:
        p_lead = lead

    if not av_demand is None:
        p_av_demand = av_demand

    if not c_holding is None:
        p_c_holding = c_holding

    if not c_shortage is None:
        p_c_shortage = c_shortage

    if not current_inv is None:
        p_current_inv = current_inv

    if not c_fixed_order is None:
        p_c_fixed_order = c_fixed_order

    if not outstanding_deliveries is None:
        p_outstanding_deliveries = outstanding_deliveries


def optimal_quantities():

    for i in range(num_i):
        holding_piecewise_objectives(i)
        shortage_objective(i)
        X_fixed[i].Obj = p_c_fixed_order[i]

    model.addConstr(quicksum(X_holding[i] for i in X_holding) <= p_stock_warehouse)  # ct max capacity at warehouse
    model.addConstrs(X_holding[i] == X_shortage[i] for i in X_holding)  # ct(i) hilfsvariable constraint
    model.addConstrs(X_holding[i] <= X_fixed[i] * p_stock_warehouse for i in X_holding)  # ct fixed order costs

    model.optimize()
    # model.printAttr('x')
    final = []
    for i in range(num_i):
        final.append(X_holding.get(i).X)
    return final
