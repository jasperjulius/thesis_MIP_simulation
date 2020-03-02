import matplotlib.pyplot as plt
from combine_graphs import combine
from matplotlib import rc
from matplotlib.pyplot import MaxNLocator

rc('text', usetex=True)

def expected_invs():
    x = []
    start = L
    for t in range(start, L * 2 + 1):  # how many periods into future? aktuell: bei L=2 => range(2,4) => 2,3
        x.append(current_inv - mu * (t + 1))
    return x


# f: return list of x-coordinates for one expected inventory
def list_x_single(inv, max):
    return [0, -inv, max]


# f: return list of x-coordinates for multiple expected inventories
def list_x_multiple(invs, max):
    invs = [-i for i in invs if i < 0]
    return [0, invs[:], max]


# f: return list of y coordinates for given list of x coordinates
def list_y_single(list_x):
    return [list_x[1] * s, 0, (list_x[2] - list_x[1]) * h]


# f: return list of y coordinates for combined function - import combine?

def costs(x):
    if x < 0:
        return x * s
    else:
        return x * h


s = 0.9
h = 0.1
L = 2
current_inv = 24
mu = 10
x_max = 40
y_max = 15
x_label = "amount sent to retailer $i$"
figure1 = plt.figure(1, figsize=(6.4, 6.8))
invs = expected_invs()

chart_multiple = figure1.add_subplot(211)
chart_multiple.axis([0, x_max, 0, 12])
chart_multiple.set_xlabel(x_label)
chart_multiple.set_ylabel("$S_{i, t}(x_i) + H_{i, t}(x_i)$ for $t \in \{ 2, 3, 4\}$")
lists_x = [list_x_single(i, x_max) for i in invs]
lists_y = [list_y_single(i) for i in lists_x]
colors = [(23 / 255, 118 / 255, 182 / 255), (1, 0.5, 0), (39 / 255, 163 / 255, 37 / 255)]
for c, x, y in zip(colors, lists_x, lists_y):
    chart_multiple.plot(x, y, "--", color=c)

colors.reverse()
colors.append("b")
colors.reverse()

y_max_combined = 40
chart_combined = figure1.add_subplot(212)
chart_combined.axis([0, x_max, 0, y_max_combined])
chart_combined.set_xlabel(x_label)
chart_combined.set_ylabel("$\sum_{t \in {2, 3, 4}} (S_{i, t}(x_i) + H_{i, t}(x_i))$")
pairs = list(map(list, zip(lists_x, lists_y)))
lc = [list(zip(*i)) for i in pairs]
one_list_combined = combine(lc[0], 1, lc[1], 1, lc[2], 1)
list_x, list_y = zip(*one_list_combined)
chart_combined.plot(list_x, list_y, "r")
for c, x, y in zip(colors, list_x, list_y):
    y_min = y / y_max_combined
    chart_combined.axvline(x=x, ymin=y_min, ls=':', color=c)
# plt.show()
# figure1.savefig("./multicombined")
plt.clf()

figure2 = plt.figure(2, figsize=(6.4, 3.8))
chart_single = figure2.add_subplot(111)
chart_single.axis([0, x_max, 0, 12])
chart_single.set_xlabel(x_label)
chart_single.set_ylabel("$S_{i, t}(x_i) + H_{i, t}(x_i)$ for $t = 2$")
chart_single.plot(lists_x[0], lists_y[0], "--")
# plt.show()
# figure2.savefig("./single")
plt.clf()

figure3 = plt.figure(3, figsize=(4.8, 4.4))
chart_fcfs = figure3.add_subplot(111)
chart_fcfs.axis([-1, 0.1, 0, 27])
chart_fcfs.set_xlabel("period $t$", fontsize=14)
chart_fcfs.set_ylabel("inventory", fontsize=14)
chart_fcfs.xaxis.set_major_locator(MaxNLocator(integer=True))
chart_fcfs.plot([-1, 0], [25, 3])
chart_fcfs.plot([-1, 0.1], [17, 17], "--", color="orange")
chart_fcfs.yaxis.set_ticks([3, 17, 25])
chart_fcfs.yaxis.set_ticklabels(["$IP_i$", "$R_i$", "$IP_i + d$"], fontsize=14)
plt.show()
figure3.savefig("./fcfs")
# plt.clf()

figure3 = plt.figure(3, figsize=(6.4, 3.8))
chart_fcfs = figure3.add_subplot(111)
# continue: final figure as in power point (plus estimated demands? or second one)?


