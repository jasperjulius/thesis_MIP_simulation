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
# todo: (probably never) excel - same same comparison fortführen - warum ist die neue schlechter als die alte?

# IN_t = IN_t-1 - mu_t-1 + O_t

# josef: lead time = 0 auch als case? erstmal nicht wichtig, L=2 ist okay! Q eoq auch gut
#    retailer mit unterschiedichen lead times auch als case? wenn ja, wie wird dann vorausgerechnet? kriegt jeder retailer sein eigenes zeitfenster(->ja)?
# einleitung, literatur,
# rückwärtssuche (für aktuelle papers zum thema): wer zitiert zB. gallego2007?, axsäter

first_row = 4

s1 = rgen.R("4er 10k low var mip", (15, 39), (30, 55), (30, 55), 4, 4, 4, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)
s2 = rgen.R("4er 10k low var fifo", (50, 70), (18, 38), (18, 38), 4, 4, 4, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)
s3 = rgen.R("4er 10k low var mip low ratio", (15, 39), (30, 55), (30, 55), 4, 4, 4, repeat=1, high_c_shortage=False, high_var=False, run_me_as=0)
s4 = rgen.R("4er 10k low var fifo low ratio", (50, 70), (18, 38), (18, 38), 4, 4, 4, repeat=1, high_c_shortage=False, high_var=False, run_me_as=0)

schwankungen1 = rgen.R("schwankungen 20k mip low var", (15, 15), (40, 40), (40, 40), 4, 4, 4, repeat=20, high_c_shortage=False, high_var=False, run_me_as=0)
schwankungen2 = rgen.R("schwankungen 20k mip high var", (15, 15), (40, 40), (40, 40), 4, 4, 4, repeat=20, high_c_shortage=False, high_var=True, run_me_as=0)

# next block to run for low var
sl1 = rgen.R("20k low var mip", (12, 21), (26, 56), (26, 56), 3, 5, 5, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)
sl2 = rgen.R("20k low var fifo", (55, 61), (23, 33), (23, 33), 1, 1, 1, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0, fifo=True)
sl3 = rgen.R("20k low var mip low ratio", (12, 21), (26, 56), (26, 56), 3, 5, 5, repeat=1, high_c_shortage=False, high_var=False, run_me_as=0)
sl4 = rgen.R("20k low var fifo low ratio", (55, 61), (19, 25), (19, 25), 1, 1, 1, repeat=1, high_c_shortage=False, high_var=False, run_me_as=0, fifo=True)

# todo: not 100% sure about values
# high ratio
sh5 = rgen.R("20k high var mip", (15, 35), (30, 55), (30, 55), 4, 4, 4, repeat=1, high_c_shortage=True, high_var=True, run_me_as=0)
sh6 = rgen.R("20k high var fifo", (50, 80), (20, 40), (20, 50), 2, 2, 2, repeat=1, high_c_shortage=True, high_var=True, run_me_as=0, fifo=True)
# low ratio
sl9 = rgen.R("10k 10er high var low mip", (5, 30), (10, 80), (10, 80), 5, 10, 10, repeat=1, high_c_shortage=False, high_var=True, run_me_as=3)


s7 = rgen.R("4er schritte 10k high var mip low ratio", (15, 35), (30, 55), (30, 55), 4, 4, 4, repeat=1, high_c_shortage=False, high_var=True, run_me_as=0)
s8 = rgen.R("4er schritte 10k high var fifo low ratio", (50, 80), (20, 40), (20, 50), 2, 2, 2, repeat=1, high_c_shortage=False, high_var=True, run_me_as=0, fifo=True)

scenarios = [sl1, sl2, sl3, sl4]

length = 20100
warm_up = 100
lengths = {100: 'short', 1000: 'mid', 10000: 'long'}

for scenario in scenarios:

    if scenario.duration < 100:
        temp_name = 'short'
    elif scenario.duration < 1000:
        temp_name = 'mid'
    elif scenario.duration < 10000:
        temp_name = 'long'
    else:
        temp_name = 'reeeally long'

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

        settings.combine = True
        settings.random = False  # todo: kann raus
        settings.no_d = False  # todo: kann raus
        fifo = scenario.fifo
        sim.run(FIFO=fifo)

        after1 = time.time()
        print_times()
        results_mip = sim.collect_statistics()
        sim.reset()
        print_results_to_sheet(results_mip, sheet, current[3], 7)
        pre2 = time.time()

        settings.combine = False
        settings.random = False
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
    name = "generated_sheets/the real deal/" + str(scenario.number) + ".xlsx"
    wb.save(name)
