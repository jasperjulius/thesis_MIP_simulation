import simulation
import time
from math import ceil
import openpyxl

sims = []

total_fifo = 0
total_mip = 0
reps = 1
start_time = time.time()
exec_times = []
last_time = 0

wb = openpyxl.load_workbook('/Users/jasperinho/PycharmProjects/thesis_MIP/analysis_first.xlsx')
print(wb.sheetnames)
sheet = wb[wb.sheetnames[0]]

for period in range(reps):

    print(period / reps)
    sim = simulation.Simulation(length=100, stock=100, stochastic=True)
    sim.run(FIFO=False)

    after1 = time.time()

    results_mip = sim.collect_statistics()
    sim.reset()

    print("Single execution times - ub, average time: ", [sum(i) / len(i) for i in zip(
        *sim.times)])  # todo: josef: wieso geht inventory wh immer weiter runter?
    number_intervals = 10
    interval_size = ceil(len(sim.times) / number_intervals)
    for interval in range(number_intervals):
        lb = interval * interval_size
        ub = (interval + 1) * interval_size
        if ub > len(sim.times):
            ub = len(sim.times)
        if not ub - lb == 0:
            print("interval: ", interval, "average: ", [sum(i[lb:ub]) / (ub - lb) for i in zip(*sim.times)])

    print("last: ", [sum(i[-interval_size:]) / interval_size for i in zip(*sim.times)])

    sim.run(FIFO=True)
    results_fifo = sim.collect_statistics()

    after2 = time.time()

    if period is 0:
        exec_times.append((after1 - start_time, after2 - after1))
    else:
        exec_times.append((after1 - last_time, after2 - after1))
    last_time = after2
    # print("(mip-based simulation, fifo simulation)", exec_times)


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
print("\nresults_mip:", results_mip, " \nresults_fifo:", results_fifo)
print("total costs in - mip:", round(total_mip, 2), "in fifo:", round(total_fifo, 2))
print("exec_times: ", exec_times)

diffs = []
diffs_percent = []
for i, j in sims:
    diffs.append(round(i - j, 2))
    diffs_percent.append(round(i / j, 4) * 100)
print(diffs)
print(diffs_percent[0], 'percent')
