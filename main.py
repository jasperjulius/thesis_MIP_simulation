import simulation
import time
import openpyxl
import r as rgen
from math import trunc


def print_results_to_sheet(results, sheet, offset_row, start_column):
    for i in range(len(results)):
        for j in range(len(results[i])):
            sheet.cell(row=first_row + offset_row, column=start_column + 3 * j + i, value=round(results[i][j], 2))


# !!! bug in warehouse.reset: schwankungen nochmal betrachten
# nach umstellung auf neg_binomial demand sind keine schwankungen mehr bei mip, sondern bei FIFO bei werten von warehouse.R um 40

# todo: fixed order costs gibt's nicht, sondern order setup costs, die beim retailer anfallen fürs bestellen
#  fragestellung: wie häufig wird er im zeitraum (von t = 0 bis t = 2*L) nochmal bestellen?

# todo: avInv berechnung umstellen, einfach inventory im zeitpunkt t nehmen für gesamte periode
#   dazu nimmt man pyhs_inv_t = phys_inv_t-1 - demand_t-1 + pending arrivals_t, und speichert die phys_invs ab
#   das gleiche muss auch im modell wiedergespiegelt werden, und im MIP

# todo: backlog B, pending deliveries als Q, IP einmal reinnehmen, E()-funktion gerade biegen
# todo: literatur für präsentation

exec_times = []
first_row = 4
wb = openpyxl.load_workbook(
    '/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/templates/template short.xlsx',
    read_only=False)
length = 1000

sheet = wb[wb.sheetnames[0]]
sheet["AH4"] = length
robj = rgen.R(20, 20, 20, 30, 30, 30, 3, 3, 3)
robj_repeat = rgen.R(20, 0, 0, 60, 0, 0, 10, 1, 1, repeat=10)  # todo: test, um schwankungen zu monitoren

last_time = time.time()
r = robj_repeat.r_same()   # todo: hier

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
    sheet["D%d" % (first_row + current[3])] = str(sim.warehouse.retailers[0].seed) +","+ str(sim.warehouse.retailers[1].seed)
    sim.run(FIFO=False)
    after1 = time.time()
    results_mip = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_mip, sheet, current[3], 7)

    sim.run(FIFO=True)
    results_fifo = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_fifo, sheet, current[3], 18)
    # print(results_mip, results_fifo)
    after2 = time.time()

    sheet["E%d" % (first_row + current[3])] = after1 - last_time
    sheet["F%d" % (first_row + current[3])] = after2 - after1
    last_time = after2

wb.save("generated_sheets/current.xlsx")
