import simulation
import time

sims = []

total_fifo = 0
total_mip = 0
reps = 1
start_time = time.time()
exec_times = []
last_time = 0
for period in range(reps):

    print(period / reps)
    sim = simulation.Simulation(length=400, stock=100, stochastic=True)
    sim.run(FIFO=False)
    after1 = time.time()
    results_mip = sim.collect_statistics()
    sim.reset()
    print("TIMES: ", sim.times, "\naverage: ", sum(sim.times) / len(sim.times)) #todo: josef: wieso dauert die execution immer länger?
    interval_size = 20
    # for interval in range(int(sim.length / interval_size)):
    #   print("interval: ", interval, "average: ",
    #        sum(sim.times[interval * interval_size:interval * (interval_size + 1)]) / interval_size)
    sim.run(FIFO=True)
    results_fifo = sim.collect_statistics()
    after2 = time.time()

    if period is 0:
        exec_times.append((after1 - start_time, after2 - after1))
    else:
        exec_times.append((after1 - last_time, after2 - after1))
    last_time = after2
    print(exec_times)
    results_difference = []  # mip - fifo
    results_percent = []

    for i, j in zip(results_mip, results_fifo):

        temp = []
        temp2 = []

        for r in range(len(i)):
            total_mip += i[r]
            total_fifo += j[r]
            temp.append(i[r] - j[r])
            if j[r] is not 0:
                temp2.append(i[r] / j[r])
            else:
                temp2.append((i[r], j[r]))

        results_difference.append(temp)
        results_percent.append(temp2)

    sims.append((total_mip, total_fifo))

diffs = []
diffs_percent = []
for i, j in sims:
    diffs.append(round(i - j, 2))
    diffs_percent.append(round(i / j, 2))
# print(diffs)
# print(diffs_percent)
