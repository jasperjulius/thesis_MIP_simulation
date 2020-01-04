class R:

    def __init__(self, R0, R1, R2, R0max, R1max, R2max, step0, step1, step2):
        self.R0 = R0
        self.R1 = R1
        self.R2 = R2
        self.R0max = R0max
        self.R1max = R1max
        self.R2max = R2max
        self.step0 = step0
        self.step1 = step1
        self.step2 = step2
        self.duration = len(range(self.R0, self.R0max + 1, self.step0))*len(range(self.R1, self.R1max + 1, self.step1))*len(range(self.R2, self.R2max + 1, self.step2))

    def r(self):
        i = 0
        for r0 in range(self.R0, self.R0max + 1, self.step0):
            for r1 in range(self.R1, self.R1max + 1, self.step1):
                for r2 in range(self.R2, self.R2max + 1, self.step2):
                    yield (r0, r1, r2, i)
                    i += 1
