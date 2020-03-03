# -------------------------------------------------------------------------------
# represents one scenario, consisting of parameter settings (high or low shortage costs, high or low variance, which lead times, ...)
# and a generator object returning all combinations of Rs that should be tested for this scenario
# -------------------------------------------------------------------------------
import global_settings as global_settings
import pickle
from simulation import binomial
from simulation import neg_binomial


def name_gen(name, L0, Li, var, c_s, h0):
    temp = name + " L" + str(L0) + "-" + str(Li)+ ", "
    if var:
        temp += "high var, "
    else:
        temp += "low var, "
    if c_s:
        temp += "high c_s, "
    else:
        temp += "low c_s, "
    if h0 == 0.1:
        temp += "high h0"
    elif h0 == 0.05:
        temp += "low h0"
    else:
        raise Exception("h0 neither 0.1 nor 0.05")
    return temp


class Scenario:

    def __init__(self, name, length=50000, warm_up=100, r0=None, step0=15, step1=1, step2=1, repeat=1, high_var=True,
                 high_c_shortage=True, run_me_as=2, settings={}):

        self.length = length
        self.warm_up = warm_up
        if high_var:
            with open("demands_high.txt", "rb") as f:
                self.demands = pickle.load(f)
            self.distribution = neg_binomial(20, 2/3)
        else:
            with open("demands_low.txt", "rb") as f:
                self.demands = pickle.load(f)
            self.distribution = binomial(20, 0.5)

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
        if self.Li == 2:
            high = (0, 105), (20, 74), (20, 74)
            low = (0, 105), (20, 64), (20, 64)
        elif self.Li == 1:
            high = (0, 135), (10, 74), (10, 74)
            low = (0, 135), (10, 64), (10, 64)
        elif self.Li == 3:
            high = (0, 75), (30, 74), (30, 74)
            low = (0, 75), (30, 64), (30, 64)
        else:
            raise Exception("scenario: Li was neither 1, 2, or 3 - no borders can be defined - Li:", self.Li)
        if high_var:
            R0, R1, R2 = high
        else:
            R0, R1, R2 = low
        if r0 is not None:
            R0 = r0
        self.run_me_as = run_me_as
        self.name = name_gen(name, self.L0, self.Li, high_var, self.high_c_shortage, self.h0)
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
