import simulation
import time
import openpyxl
import r as rgen
from math import trunc
import mytimes
import settings


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

# todo: literatur für präsentation

# fixed order costs gibt's nicht, sondern order setup costs, die beim retailer anfallen fürs bestellen
#  fragestellung: wie häufig wird er im zeitraum (von t = 0 bis t = 2*L) nochmal bestellen?
# todo: excel - same same comparison fortführen - warum ist die neue schlechter als die alte?

# todo: rta - in MIP, solving the model is currently taking up 75% of computation time - improvement possible?

# pyhs_inv_t = phys_inv_t-1 - demand_t-1 + pending arrivals_t


# josef: fifo - neue Implementierung mit "not full order has to be delivered, but multiple of q" - viable? yes!
# backorders tracken in neuer var D, wird priorisiert in FIFO
#    demand with lower fluctuation -> MIP wieder besser!
# b zu h viel extremer, var in variation coeficient
# warm-up (zukunft)
# josef: lead time = 0 auch als case? erstmal nicht wichtig, L=2 ist okay! Q eoq auch gut
#    retailer mit unterschiedichen lead times auch als case? wenn ja, wie wird dann vorausgerechnet? kriegt jeder retailer sein eigenes zeitfenster?
# josef:  pending deliveries als Q? habe es erstmal O genannt, wegen Q aus R, Q: okay
# einleitung, literatur,
# rückwärtssuche: wer zitiert zB. gallego?, axsäter

first_row = 4
wb = openpyxl.load_workbook(
    '/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/templates/template short.xlsx',
    read_only=False)
sheet = wb[wb.sheetnames[0]]


# robj = rgen.R(20, 15, 15, 30, 25, 25, 1, 1, 1)
robj = rgen.R(20, 0, 0, 50, 0, 0, 10, 1, 1, repeat=5)
# r = robj.r()
r = robj.r_same()

length = 5000
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
    settings.order_setup = False
    sim.run(FIFO=False)
    after1 = time.time()

    print_times()

    results_mip = sim.collect_statistics()
    sim.reset()

    print_results_to_sheet(results_mip, sheet, current[3], 7)
    pre2 = time.time()
    settings.order_setup = False
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
