class R:

    def __init__(self, R0, R1, R2, R0max, R1max, R2max, step0, step1, step2, repeat=1):
        self.repeat = repeat
        self.R0 = R0
        self.R1 = R1
        self.R2 = R2
        self.R0max = R0max
        self.R1max = R1max
        self.R2max = R2max
        self.step0 = step0
        self.step1 = step1
        self.step2 = step2
        self.duration = len(range(self.R0, self.R0max + 1, self.step0)) * len(
            range(self.R1, self.R1max + 1, self.step1)) * len(range(self.R2, self.R2max + 1, self.step2)) * self.repeat

    def r(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for r2 in range(self.R2, self.R2max + 1, self.step2):
                    for j in range(self.repeat):
                        yield (r0, r1, r2, i)
                        i += 1

    def r_same(self):
        self.duration = len(range(self.R0, self.R0max + 1, self.step0)) * self.repeat
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for j in range(self.repeat):
                yield (r0, r0, r0, i)
                i += 1
