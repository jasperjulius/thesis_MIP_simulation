def r(R0, R1, R2, R0max, R1max, R2max, step0, step1, step2):
    i = 0
    for r0 in range(R0, R0max + 1, step0):
        for r1 in range(R1, R1max + 1, step1):
            for r2 in range(R2, R2max + 1, step2):
                yield (r0, r1, r2, i)
                i += 1
