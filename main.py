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

# IN_t = IN_t-1 - mu_t-1 + O_t

# josef: lead time = 0 auch als case? erstmal nicht wichtig, L=2 ist okay! Q eoq auch gut
#    retailer mit unterschiedichen lead times auch als case? wenn ja, wie wird dann vorausgerechnet? kriegt jeder retailer sein eigenes zeitfenster(->ja)?
# einleitung, literatur,
# rückwärtssuche (für aktuelle papers zum thema): wer zitiert zB. gallego2007?, axsäter

first_row = 4

# robj = rgen.R(10, 10, 10, 20, 20, 20, 1, 1, 1, repeat=2)
s3 = rgen.R(3, (20, 40), (10, 20), (10, 20), 4, 4, 4, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)

scenarios = [s3]

length = 1100
warm_up = 100
lengths = {100: 'short', 1000: 'mid', 10000: 'long'}

for scenario in scenarios:

    if scenario.duration < 100:
        temp_name = 'short'
    elif scenario.duration < 1000:
        temp_name = 'mid'
    else:
        temp_name = 'long'

    wb = openpyxl.load_workbook(
        '/Users/jasperinho/PycharmProjects/thesis_MIP/generated_sheets/templates/template ' + temp_name + '.xlsx',
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
