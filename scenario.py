class Scenario:

    def __init__(self, number, length, warm_up, R0, R1, R2, step0, step1, step2, repeat=1, high_var=True,
                 high_c_shortage=True, fifo=False, run_me_as=0, demands=None, distribution=None, settings={}):
        self.length = length
        self.warm_up = warm_up
        self.demands = demands
        self.distribution = distribution
        self.high_c_shortage = high_c_shortage
        self.L0 = 2
        for key in settings:
            if key == "L0":
                self.L0 = settings[key]
            if key == "high_c_shortage":
                self.high_c_shortage = settings[key]
        self.fifo = fifo
        self.run_me_as = run_me_as
        self.number = number
        self.high_var = high_var

        self.repeat = repeat
        self.R0 = R0[0]
        self.R1 = R1[0]
        self.R2 = R2[0]
        self.R0max = R0[1]
        self.R1max = R1[1]
        self.R2max = R2[1]
        self.step0 = step0
        self.step1 = step1
        self.step2 = step2
        self.duration = len(range(self.R0, self.R0max + 1, self.step0)) * len(
            range(self.R1, self.R1max + 1, self.step1)) * len(range(self.R2, self.R2max + 1, self.step2)) * self.repeat

    def get_iterator(self):
        if self.run_me_as == 0:
            return self.r()
        if self.run_me_as == 1:
            return self.r_same()
        if self.run_me_as == 2:
            return self.r_connected_retailers()
        if self.run_me_as == 3:
            return self.r_sum()

    def r(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for r2 in range(self.R2, self.R2max + 1, self.step2):
                    for j in range(self.repeat):
                        yield (r0, r1, r2, i)
                        i += 1

    def r_sum(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for r2 in range(self.R2, self.R2max + 1, self.step2):
                    for j in range(self.repeat):
                        if 85 < r1+r2 < 105:
                            yield (r0, r1, r2, i)
                            i += 1

    def r_connected_retailers(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for j in range(self.repeat):
                    yield (r0, r1, r1, i)
                    i += 1

    def r_same(self, offset=0):
        self.duration = len(range(self.R0, self.R0max + 1, self.step0)) * self.repeat
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for j in range(self.repeat):
                yield (r0, r0 - offset, r0 - offset, i)
                i += 1
