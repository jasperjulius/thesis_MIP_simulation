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

# fixed order costs gibt's nicht, sondern order setup costs, die beim retailer anfallen fürs bestellen
#  fragestellung: wie häufig wird er im zeitraum (von t = 0 bis t = 2*L) nochmal bestellen?

# todo: change order of execution in simulation according to axsäter 2002
# todo: cost calculation: should probably apply to inventory at the end of the period, basically the same as at the beginning of period before arrivals
# todo: reflect in MIP; estimated inventories should be at end of period
# todo: was nehmen für holding costs warehouse?
# todo: implement alternative to MIP that utilizes same thought but only with x_i as positive multiple of Q_i

# todo: extend main, excel sheets to run three simulations (mip, mip without splittig, fcfs)
# todo: parallelize - 8-core

# IN_t = IN_t-1 - mu_t-1 + O_t

# josef: lead time = 0 auch als case? erstmal nicht wichtig, L=2 ist okay! Q eoq auch gut
#    retailer mit unterschiedichen lead times auch als case? wenn ja, wie wird dann vorausgerechnet? kriegt jeder retailer sein eigenes zeitfenster(->ja)?
# einleitung, literatur,
# rückwärtssuche (für aktuelle papers zum thema): wer zitiert zB. gallego2007?, axsäter

first_row = 4

schwankungen1 = rgen.R("schwankungen 20k mip low var", (15, 15), (40, 40), (40, 40), 4, 4, 4, repeat=20, high_c_shortage=False, high_var=False, run_me_as=0)
schwankungen2 = rgen.R("schwankungen 20k mip high var", (25, 40), (40, 40), (40, 40), 15, 5, 5, repeat=30, high_c_shortage=False, high_var=True, run_me_as=0)
schwankungen3 = rgen.R("schwankungen 20k mip high var mip", (10, 10), (10, 10), (76, 76), 1, 1, 1, repeat=30, high_c_shortage=False, high_var=True, run_me_as=0)
schwankungen4 = rgen.R("20k fifo schwnkungen low", (58, 58), (26, 26), (26, 26), 1, 1, 1, repeat=30, high_c_shortage=True, high_var=False, run_me_as=0, fifo=True)
schwankungen5 = rgen.R("20k fifo schwnkungen low - low", (58, 58), (26, 26), (26, 26), 1, 1, 1, repeat=30, high_c_shortage=False, high_var=False, run_me_as=0, fifo=True)

# low var
# high ratio
low1 = rgen.R("20k mip low_var high_s rad3", (0, 10), (0, 15), (65, 80), 2, 3, 3, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)
# low_final2 = rgen.R("100k low var fifo ", (55, 61), (23, 29), (23, 29), 1, 1, 1, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0, fifo=True)
# low ratio
low3 = rgen.R("20k mip low_var mip low_s rad3", (4, 8), (0, 6), (65, 75), 1, 2, 2, repeat=1, high_c_shortage=False, high_var=False, run_me_as=0)
# low_final4 = rgen.R("100k low var fifo low ratio", (57, 60), (20, 22), (20, 22), 1, 1, 1, repeat=1, high_c_shortage=False, high_var=False, run_me_as=0, fifo=True)

# high var
# high ratio
high1 = rgen.R("20k mip high_var mip high_s rad3", (0, 6), (0, 15), (75, 85), 1, 3, 2, repeat=1, high_c_shortage=True, high_var=True, run_me_as=0)
# high_final2 = rgen.R("100k high var fifo", (55, 61), (29, 39), (29, 37), 1, 1, 1, repeat=1, high_c_shortage=True, high_var=True, run_me_as=0, fifo=True)
# low ratio
high3 = rgen.R("20k mip high_var mip low_s rad3", (0, 6), (0, 10), (71, 79), 1, 3, 2, repeat=1, high_c_shortage=False, high_var=True, run_me_as=0)
# high_final4 = rgen.R("100k high var fifo - low", (55, 61), (21, 31), (21, 31), 1, 1, 1, repeat=1, high_c_shortage=False, high_var=True, run_me_as=0, fifo=True)

# new mip scenarios
teste1 = rgen.R("new mip - first test", (4, 20), (30, 60), (30, 60), 2, 3, 3, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)
teste2 = rgen.R("new mip no splitting - second test", (10, 40), (30, 60), (30, 60), 10, 20, 20, repeat=1, high_c_shortage=True, high_var=False, run_me_as=0)


scenarios = [teste2]

length = 2100
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

        if not scenario.fifo:
            pre1 = time.time()
            # settings.ignore = True
            settings.no_batch_splitting = True
            settings.combine = True
            settings.random = False  # todo: kann raus
            settings.no_d = False  # todo: kann raus
            sim.run(FIFO=False)

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
        if not scenario.fifo:
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
    name = "generated_sheets/after_mid/" + str(scenario.number) + ".xlsx"
    wb.save(name)
