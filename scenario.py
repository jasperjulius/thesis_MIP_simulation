# -------------------------------------------------------------------------------
# represents one scenario, consisting of parameter settings (high or low shortage costs, high or low variance, which lead times, ...)
# and a generator object returning all combinations of Rs that should be tested for this scenario
# -------------------------------------------------------------------------------
import global_settings as global_settings
class Scenario:

    def __init__(self, name, length, warm_up, R0, R1, R2, step0, step1, step2, repeat=1, high_var=True,
                 high_c_shortage=True, run_me_as=2, demands=None, distribution=None, settings={}):
        self.length = length
        self.warm_up = warm_up
        self.demands = demands  # multiple lists (one for each retailer) of random demands
        self.distribution = distribution    # info about the underlying distribution

        self.h0 = 0.1
        self.L0 = 2
        self.Li = 2
        self.high_c_shortage = high_c_shortage
        for key in settings:
            if key == "h0":
                self.h0 = settings[key]
            if key == "L0":
                self.L0 = settings[key]
            if key == "Li":
                self.Li = settings[key]
            if key == "high_c_shortage":
                self.high_c_shortage = settings[key]

        self.run_me_as = run_me_as
        self.name = name
        self.high_var = high_var
        global_settings.high_var = self.high_var
        global_settings.high_c_shortage = self.high_c_shortage
        self.repeat = repeat    # runs same setting multiple times - was used for testing

        self.R0 = R0[0]  # lower bounds
        self.R1 = R1[0]
        self.R2 = R2[0]
        self.R0max = R0[1]  # upper bounds
        self.R1max = R1[1]
        self.R2max = R2[1]
        self.step0 = step0   # step sizes between the lower bound and upper bound
        self.step1 = step1
        self.step2 = step2

        self.duration = len(range(self.R0, self.R0max + 1, self.step0)) * len(
            range(self.R1, self.R1max + 1, self.step1)) * len(range(self.R2, self.R2max + 1, self.step2)) * self.repeat

    # returns one of the iterators below based on the setting made
    #   if not specified, self.run_me_as is set to 2
    def get_iterator(self):
        if self.run_me_as == 0:
            return self.r()
        if self.run_me_as == 1:
            return self.r_same()
        if self.run_me_as == 2:
            return self.r_connected_retailers()


    # first generator - gives all possible combinations of (R0, R1, R2)
    def r(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for r2 in range(self.R2, self.R2max + 1, self.step2):
                    for j in range(self.repeat):
                        yield (r0, r1, r2, i)
                        i += 1

    # second generator - gives all possible combinations of (R0, R1, R2), where R1 = R2
    # used when retailers are identical, which is always the case
    def r_connected_retailers(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for j in range(self.repeat):
                    yield (r0, r1, r1, i)
                    i += 1

    # second generator - gives all possible combinations of (R0, R1, R2), where R0 = R1 = R2
    # was previously used for testing purposes
    def r_same(self, offset=0):
        self.duration = len(range(self.R0, self.R0max + 1, self.step0)) * self.repeat
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for j in range(self.repeat):
                yield (r0, r0 - offset, r0 - offset, i)
                i += 1

    def getRanges(self):
        return (self.R0, self.R0max), (self.R1, self.R1max), (self.R2, self.R2max)
