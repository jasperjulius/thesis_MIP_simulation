import simulation
import time
import openpyxl
import r as rgen
from math import trunc
import mytimes


def print_results_to_sheet(results, sheet, offset_row, start_column):
    for i in range(len(results)):
        for j in range(len(results[i])):
            sheet.cell(row=first_row + offset_row, column=start_column + 3 * j + i, value=round(results[i][j], 2))


def print_times():
    round_by = 3
    summ = 0
    sums = []
    for num, i in enumerate(mytimes.exec_groups):
        print(num, [round(x, round_by)for x in i])
        for j in i:
            summ += j
    for i in zip(*mytimes.exec_groups):
        sums.append(sum(i))
    sums = [round(i, round_by) for i in sums]
    print("\nS", sums)
    print("total sum: ", round(summ, round_by))
    print("\n")


# schwankungen behoben, jetzt ist FIFO besser als MIP...

# todo: fixed order costs gibt's nicht, sondern order setup costs, die beim retailer anfallen fürs bestellen
#  fragestellung: wie häufig wird er im zeitraum (von t = 0 bis t = 2*L) nochmal bestellen?
# todo: rta - in MIP, solving the model is currently taking up 75% of computation time - improvement possible?


# todo: avInv umstellung im modell umsetzen
# todo: backlog B, pending deliveries als Q, IP einmal reinnehmen, E()-funktion gerade biegen
# pyhs_inv_t = phys_inv_t-1 - demand_t-1 + pending arrivals_t
# todo: literatur für präsentation

first_row = 4
wb = openpyxl.load_workbook(
    '/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/templates/template short.xlsx',
    read_only=False)
sheet = wb[wb.sheetnames[0]]


# robj = rgen.R(20, 20, 20, 50, 50, 50, 2, 2, 2)
robj = rgen.R(20, 0, 0, 20, 0, 0, 1, 1, 1, repeat=1)
# r = robj.r()
r = robj.r_same()

length = 10000
sheet["AH4"] = length
for current in r:
    sim = simulation.Simulation(length=length, stock=10, stochastic=True, thomas=False)
    print(current)
    print(round(((current[3] / robj.duration) * 100), 2), "%")
    # r1 = sim.warehouse.retailers[0]
    # r1.c_holding = 0.3
    # r1.c_shortage = 4

    sim.warehouse.R = current[0]
    sim.warehouse.retailers[0].R = current[1]
    sim.warehouse.retailers[1].R = current[2]

    sheet["A%d" % (first_row + current[3])] = sim.warehouse.R
    sheet["B%d" % (first_row + current[3])] = sim.warehouse.retailers[0].R
    sheet["C%d" % (first_row + current[3])] = sim.warehouse.retailers[1].R
    sheet["D%d" % (first_row + current[3])] = str(sim.warehouse.retailers[0].seed) + "," + str(
        sim.warehouse.retailers[1].seed)
    pre1 = time.time()
    sim.run(FIFO=False)
    after1 = time.time()

    print_times()

    results_mip = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_mip, sheet, current[3], 7)
    pre2 = time.time()
    sim.run(FIFO=True)
    after2 = time.time()

    print_times()

    results_fifo = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_fifo, sheet, current[3], 18)
    # print(results_mip, results_fifo)

    sheet["E%d" % (first_row + current[3])] = after1 - pre1
    sheet["F%d" % (first_row + current[3])] = after2 - pre2

wb.save("generated_sheets/current.xlsx")
