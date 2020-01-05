import MIP as mip
import retailer as rt
import warehouse as wh
import numpy.random as rand


class Simulation:

    def __init__(self, num_retailers=2, length=100, stock=100, stochastic=True, thomas=False):
        self.length = length
        self.warehouse = wh.Warehouse(stock=stock, thomas=thomas)
        self.stats = None
        self.num_retailers = num_retailers

        for i in range(num_retailers):

            if stochastic:

                seed = rand.randint(0, 10000, 1)[0]  # todo: wieder seedfrei am ende, nur fürs testen
                rand.seed(seed)
                if not thomas:  # todo: if not thomas
                    random = rand.negative_binomial(4, 0.4, length)
                else:
                    random = rand.poisson(2 * i + 2, length)  # todo: find out parameter
                    # todo: alternatively compound poisson

            else:
                random = None

            r = rt.Retailer(i, self.length, seed=seed, demands=random, thomas=thomas)
            self.warehouse.add_retailer(r)

    def collect_statistics(self):

        rt_invs = []
        rt_demands = []
        rt_pending = []
        rt_param_h = []
        rt_param_s = []
        rt_param_fixed = []
        total_h = []
        total_s = []
        total_f = []

        # kosten warehouse

        w = self.warehouse
        total_h.append(sum(w.doc_inv) * w.c_holding)
        total_s.append(0)
        count = 0
        for i in w.doc_arrivals:
            if i > 0:
                count += 1

        total_f.append(count * w.c_fixed_order)

        for r in self.warehouse.retailers:
            rt_invs.append(r.doc_inv)
            rt_demands.append(r.demands)
            rt_pending.append(r.doc_arrivals)
            rt_param_h.append(r.c_holding)
            rt_param_s.append(r.c_shortage)
            rt_param_fixed.append(r.c_fixed_order)
        for i in range(len(rt_invs)):  # entspricht anzahl retailer
            cost_h = 0
            cost_s = 0
            cost_f = 0
            for order in rt_pending[i]:
                if order > 0:
                    cost_f += rt_param_fixed[i]

            for inv, demand in zip(rt_invs[i], rt_demands[i]):  # simplifizierte version
                if inv > 0:
                    cost_h += inv
                elif inv < 0:
                    cost_s += -inv

            total_h.append(cost_h * rt_param_h[i])
            total_s.append(cost_s * rt_param_s[i])
            total_f.append(cost_f)

        self.stats = [total_h, total_s, total_f]
        return [total_h, total_s, total_f]

    def reset(self):
        self.stats = None
        self.warehouse.reset()

    def run(self, FIFO=False, RAND=False):
        for i in range(self.length):
            # self.warehouse.print_stocks(i)
            self.warehouse.update_morning(i)
            self.warehouse.update_self()

            amounts = self.amounts_requested(self.warehouse)

            if sum(amounts) > self.warehouse.stock:  # decision rule time
                if FIFO:
                    self.fifo(amounts)  # currently only works for two retailers!
                elif RAND:
                    self.random(amounts)
                else:
                    if self.warehouse.stock is not 0:
                        model = mip.MIP()
                        model.set_params_warehouse(self.warehouse)
                        model.set_params_all_retailers(self.warehouse.retailers)
                        amounts = model.optimal_quantities()
                    else:
                        amounts = [0 for i in range(self.num_retailers)]

                    # print('SIMULATION! period:', i, 'stock_before:', self.warehouse.stock, 'quantities:', amounts)

            self.warehouse.send_stocks(amounts)
            self.warehouse.update_doc_inv()
            self.warehouse.add_stock(self.amount_requested(self.warehouse))

            # self.warehouse.print_stocks(i)
            self.warehouse.update_evening()
            # self.warehouse.print_stocks(i)

    def amounts_pre(self, amounts):  # todo: test
        # reduce to first multiple of lot possible
        stock = self.warehouse.stock
        qs = [self.warehouse.retailers[i].Q for i in range(2)]
        for i in range(len(amounts)):
            while amounts[i] > stock:
                amounts[i] = amounts[i] - qs[i]

    def random(self,
               amounts):  # BAUSTELLE - sendet zu hohe mengen randomly chooses one of the retailers to receive tha product
        for i in amounts:
            if i > self.warehouse.stock:
                i = 0

        number_retailers = len(self.warehouse.retailers)
        chosen = rand.randint(0, number_retailers - 1)
        for i in range(number_retailers):
            if not i == chosen:
                amounts[i] = 0

    def fifo(self, amounts):

        self.amounts_pre(amounts)

        def takeSecond(elem):
            return elem[1]

        ips = []
        i = 0
        stock = self.warehouse.stock

        for r in self.warehouse.retailers:
            ips.append((i, r.ip()))
            i += 1

        ips.sort(key=takeSecond)

        for num, ip in ips:
            if amounts[num] > stock:
                amounts[num] = 0
            else:
                stock -= amounts[num]

    def amount_requested(self, retailer):
        R = retailer.R
        Q = retailer.Q
        ip = retailer.ip()
        amount = 0
        while R > ip:
            amount += Q
            ip += Q
        return amount

    def amounts_requested(self, warehouse):
        a = []
        for r in warehouse.retailers:
            a.append(self.amount_requested(r))
        return a
