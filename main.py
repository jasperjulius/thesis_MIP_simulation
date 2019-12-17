import simulation
import time
import openpyxl
from r import r
from math import trunc


def print_results_to_sheet(results, sheet, offset_row, start_column):
    for i in range(len(results)):
        for j in range(len(results[i])):
            sheet.cell(row=first_row + offset_row, column=start_column + 3 * j + i, value=round(results[i][j], 2))


# todo: 1. gleiche parameter (auch R), verschiedene random values -> große schwankungen bei mip - mit höheren werten für R?
# todo 2. nach umstellung auf neg_binomial demand sind keine schwankungen mehr bei mip, sondern bei FIFO bei werten von warehouse.R um 40
# todo: alles soweit niederschreiben über implementierung - paper lesen - literaturteil thomas lesen
# todo: josef: (thomas av demand ist sehr niedrig, dadurch sind schwankungen relativ klein nehme ich an)
# todo: josef: welche richtung? mehr retailer? mehr stufen? keine bstellungen mehr, sondern jede periode mip?


exec_times = []
last_time = time.time()

first_row = 4
wb = openpyxl.load_workbook('/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/current.xlsx',
                            read_only=False)
length = 1000

sheet = wb[wb.sheetnames[0]]
sheet["AH4"] = length
r = r(30, 30, 30, 50, 50, 50, 2, 2, 2)

for current in r:

    sim = simulation.Simulation(length=length, stock=100, stochastic=True)
    print(current)

    r1 = sim.warehouse.retailers[0]
    r1.c_holding = 0.3
    r1.c_shortage = 4

    sim.warehouse.R = current[0]
    sim.warehouse.retailers[0].R = current[1]
    sim.warehouse.retailers[1].R = current[2]

    sheet["A%d" % (first_row + current[3])] = sim.warehouse.R
    sheet["B%d" % (first_row + current[3])] = sim.warehouse.retailers[0].R
    sheet["C%d" % (first_row + current[3])] = sim.warehouse.retailers[1].R
    sheet["D%d" % (first_row + current[3])] = sim.seed
    sim.run(FIFO=False)
    after1 = time.time()
    results_mip = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_mip, sheet, current[3], 7)

    sim.run(FIFO=True)
    results_fifo = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_fifo, sheet, current[3], 18)
    print(results_mip, results_fifo)
    after2 = time.time()

    sheet["E%d" % (first_row + current[3])] = after1 - last_time
    sheet["F%d" % (first_row + current[3])] = after2 - after1
    last_time = after2

wb.save("generated_sheets/current.xlsx")
