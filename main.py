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
    summ = 0
    for num, i in enumerate(mytimes.exec_groups):
        print(num, i)
        for j in i:
            summ += j
    print("SUM: ", summ)
    print("\n")


# schwankungen behoben, jetzt ist FIFO besser als MIP...

# todo: fixed order costs gibt's nicht, sondern order setup costs, die beim retailer anfallen fürs bestellen
#  fragestellung: wie häufig wird er im zeitraum (von t = 0 bis t = 2*L) nochmal bestellen?

# todo: avInv umstellung im modell umsetzen
# todo: backlog B, pending deliveries als Q, IP einmal reinnehmen, E()-funktion gerade biegen
# pyhs_inv_t = phys_inv_t-1 - demand_t-1 + pending arrivals_t

# todo: literatur für präsentation

first_row = 4
length = 30000
wb = openpyxl.load_workbook(
    '/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/templates/template short.xlsx',
    read_only=False)

sheet = wb[wb.sheetnames[0]]
sheet["AH4"] = length
# robj = rgen.R(20, 20, 20, 50, 50, 50, 2, 2, 2)
robj = rgen.R(20, 0, 0, 20, 0, 0, 1, 1, 1, repeat=1)
# r = robj.r()
r = robj.r_same()

last_time = time.time()


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
    sim.run(FIFO=True)  #todo: change to False

    print_times()

    after1 = time.time()
    results_mip = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_mip, sheet, current[3], 7)

    sim.run(FIFO=True)
    print_times()

    results_fifo = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_fifo, sheet, current[3], 18)
    # print(results_mip, results_fifo)
    after2 = time.time()

    sheet["E%d" % (first_row + current[3])] = after1 - last_time
    sheet["F%d" % (first_row + current[3])] = after2 - after1
    last_time = after2

wb.save("generated_sheets/current.xlsx")

