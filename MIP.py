import simpy
from gurobipy import *


# TODO: aktuell wird mit dem tagesmittelwert gerechnet. dies ist eine akkurate angabe bei positivem inventory an morgen und abend, aber nicht bei wechsel von pos auf neg. (iv/2*iv/d)
def holding_piecewise_objectives(X_holding, i):  # average inventory of retailer i in period t - only for t >= leadtime
    count = 0
    graph = []
    x = 0

    for t in range(p_lead[i], p_lead[i] * 2 + 1):  # how many periods into future?

        x = p_current_inv[i] + sum(p_pending_arrivals[i][:t + 1]) - p_av_demand[i] * (t + 0.5)

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


def shortage_objective(X_shortage, i):
    ip = []
    missed_deliveries = []
    total_loss = 0
    sum_missed_deliveries = 0

    for t in range(p_lead[i], p_lead[i] * 2 + 2):
        ip.append(p_current_inv[i] + sum(p_pending_arrivals[i][:t + 1]) - p_av_demand[i] * t)

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
model = Model()
model.setParam('OutputFlag', False)

p_stock_warehouse = None

p_lead = []
p_av_demand = []
p_c_holding = []
p_c_shortage = []
p_current_inv = []
p_c_fixed_order = []

# erster wert jeweils für t = 0, also "jetzt"; aktuell wird so gerechnet, als kämen deliveries first thing in the morning an, und sind somit im täglichen inventory zur berechnung der holding/shortage costs mit drin
p_pending_arrivals = []


def set_params_warehouse(warehouse):
    global p_stock_warehouse
    p_stock_warehouse = warehouse.stock


def set_params_all_retailers(retailers):
    global p_lead
    global p_av_demand
    global p_c_holding
    global p_c_shortage
    global p_current_inv
    global p_c_fixed_order
    global p_pending_arrivals

    p_lead = []
    p_av_demand = []
    p_c_holding = []
    p_c_shortage = []
    p_current_inv = []
    p_c_fixed_order = []
    p_pending_arrivals = []

    for r in retailers:
        set_params_retailer(r)


def set_params_retailer(retailer):
    p_lead.append(retailer.lead)
    p_av_demand.append(retailer.av_demand)
    p_c_holding.append(retailer.c_holding)
    p_c_shortage.append(retailer.c_shortage)
    p_current_inv.append(retailer.current_inv)
    p_c_fixed_order.append(retailer.c_fixed_order)
    p_pending_arrivals.append(retailer.pending_arrivals)


def update_params(stock_warehouse=None, lead=None, av_demand=None, c_holding=None, c_shortage=None, current_inv=None,
                  c_fixed_order=None, outstanding_deliveries=None):
    global p_stock_warehouse
    global p_lead
    global p_av_demand
    global p_c_holding
    global p_c_shortage
    global p_current_inv
    global p_c_fixed_order
    global p_pending_arrivals

    if stock_warehouse is not None:
        p_stock_warehouse = stock_warehouse

    if lead is not None:
        p_lead = lead

    if av_demand is not None:
        p_av_demand = av_demand

    if c_holding is not None:
        p_c_holding = c_holding

    if c_shortage is not None:
        p_c_shortage = c_shortage

    if current_inv is not None:
        p_current_inv = current_inv

    if c_fixed_order is not None:
        p_c_fixed_order = c_fixed_order

    if outstanding_deliveries is not None:
        p_pending_arrivals = outstanding_deliveries


def optimal_quantities():
    num_i = len(p_lead)
    X_holding = model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out')
    X_shortage = model.addVars(num_i, vtype=GRB.INTEGER, name='# sent out (helper var) ')
    X_fixed = model.addVars(num_i, vtype=GRB.BINARY, name='delivering to i')

    for i in range(num_i):
        holding_piecewise_objectives(X_holding, i)
        shortage_objective(X_shortage, i)
        X_fixed[i].Obj = p_c_fixed_order[i]

    model.addConstr(quicksum(X_holding[i] for i in X_holding) <= p_stock_warehouse)  # ct max capacity at warehouse
    model.addConstrs(X_holding[i] == X_shortage[i] for i in X_holding)  # ct(i) hilfsvariable constraint
    model.addConstrs(X_holding[i] <= X_fixed[i] * p_stock_warehouse for i in X_holding)  # ct fixed order costs

    model.optimize()
    # model.printAttr('x')
    final = []
    for i in range(num_i):
        final.append(int(X_holding.get(i).X))
    return final
