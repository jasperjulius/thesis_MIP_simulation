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
        print(num, [round(x, round_by) for x in i])
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

# todo: große frage: sind die schwankungen vertretbar? andere wahrscheinlichkeitsvertilung ausprobieren?


# todo: diese!!!
# todo: retailer 2 hat in MIP sehr hohe shortage costs, wird der gesendete amount eventuell nur hinsichtlich holding costs optimisiert? oder wird retailer 1 anderweitig bevorzugt? was da los?
#  implementierung der ds funktionert nicht in MIP, da ds in der fifo funktion erzeugt werden -> ändern! vielleicht ist es das

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

# robj = rgen.R(10, 10, 10, 20, 20, 20, 1, 1, 1, repeat=2)
s1 = rgen.R(1, 20, 20, 0, 50, 40, 0, 1, 1, 1, repeat=2, high_c_shortage=True, high_var=False, run_me_as=2)
s2 = rgen.R(2, 48, 30, 0, 70, 70, 0, 1, 1, 1, repeat=1, high_c_shortage=True, high_var=False, run_me_as=-1)
s3 = rgen.R(3, 40, 0, 0, 40, 0, 0, 10, 1, 1, repeat=20, high_c_shortage=True, high_var=False, run_me_as=1)

scenarios = [s3]

length = 3300
warm_up = 300

for scenario in scenarios:

    wb = openpyxl.load_workbook(
        '/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/templates/template short.xlsx',
        read_only=False)
    sheet = wb[wb.sheetnames[0]]
    sheet["AH4"] = length - warm_up

    r = scenario.get_r()
    for current in r:
        sim = simulation.Simulation(length=length, warm_up=warm_up, stock=60, high_var=scenario.high_var,
                                    high_c_shortage=scenario.high_c_shortage)
        print(current)
        print(round(((current[3] / scenario.duration) * 100), 2), "%")

        sim.warehouse.R = current[0]
        sim.warehouse.retailers[0].R = current[1]
        sim.warehouse.retailers[1].R = current[2]

        sheet["A%d" % (first_row + current[3])] = sim.warehouse.R
        sheet["B%d" % (first_row + current[3])] = sim.warehouse.retailers[0].R
        sheet["C%d" % (first_row + current[3])] = sim.warehouse.retailers[1].R
        sheet["D%d" % (first_row + current[3])] = str(sim.warehouse.retailers[0].seed) + "," + str(
            sim.warehouse.retailers[1].seed)
        pre1 = time.time()

        settings.random = False
        settings.order_setup = False
        settings.no_d = False
        sim.run(FIFO=False)

        after1 = time.time()
        print_times()
        results_mip = sim.collect_statistics()
        sim.reset()
        print_results_to_sheet(results_mip, sheet, current[3], 7)
        pre2 = time.time()

        settings.random = False
        settings.order_setup = False
        settings.no_d = False
        sim.run(FIFO=True)

        after2 = time.time()
        print_times()
        results_fifo = sim.collect_statistics()
        sim.reset()
        print_results_to_sheet(results_fifo, sheet, current[3], 18)
        sheet["E%d" % (first_row + current[3])] = after1 - pre1
        sheet["F%d" % (first_row + current[3])] = after2 - pre2

    sheet["AH8"] = sim.distribution[0]
    sheet["AI8"] = sim.distribution[1]
    sheet["AJ8"] = float(sim.distribution[2])
    sheet["AK8"] = float(sim.distribution[3])
    sheet["AL8"] = float(sim.distribution[4])

    sheet["AH12"] = sim.warehouse.retailers[0].c_holding
    sheet["AI12"] = sim.warehouse.retailers[0].c_shortage
    sheet["AJ12"] = sim.warehouse.retailers[1].c_holding
    sheet["Ak12"] = sim.warehouse.retailers[1].c_shortage
    name = "generated_sheets/scenario" + str(scenario.number) + ".xlsx"
    wb.save(name)
