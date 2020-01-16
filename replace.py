text = "0.99, 0.81, 1.19, 2.07, 1.51, 1.67, 2.35, 2.11, 2.28, 2.57, 2.79, 2.98, 3.15, 3.78, 3.59, 3.96, 4.05, 4.27, 4.5, 4.84, 4.91, 5.14, 5.35, 5.72, 5.79, 6.0, 6.23, 6.64, 6.65, 7.94], [7.24, 0.16, 0.43, 0.72, 1.01, 1.3, 1.58, 1.88, 2.15, 2.45, 2.71, 3.06, 3.28, 3.58, 3.85, 4.13, 4.42, 4.69, 4.97, 5.28, 5.51, 5.81, 6.07, 6.32, 6.65, 6.86, 7.15, 7.44, 7.78, 8.01"
text = text.replace(",", "")
text = text.replace(".", ",")


#  print(text)

# text2 = "aktuell für BSc. Management and Technology (\"TUM-BWL\") an der TU München eingeschrieben (42 ECTS im FachbereichInformatik )"


#  print("SKURR: ",len(text2))

def neg_bin(n, p):
    mu = n * (1 - p) / p
    var = n * (1 - p) / p ** 2
    return ("neg bin:", n, p, mu, var)


def bin(n, p):
    mu = n * p
    var = n * p * (1 - p)
    return ("bin: ", n, p, mu, var)


print(neg_bin(10, 0.5))
print(neg_bin(15, 0.6))
print(neg_bin(20, 2 / 3))

print("\n", bin(20, 0.5))
print(bin(25, 0.4))
print(bin(50, 0.2))


def get_list():
    yield [(0, 6), (10, 6), (11, 3), (20, 3), (21, 2), (30, 2)]
    yield [(-1, -1), (2, 2), (4, 6)]
    yield [(0, 20), (8, 4), (12, 0), (13, 0)]


def combine():
    list_getter = get_list()
    graph_fixed = next(list_getter)
    graph_holding = next(list_getter)
    graph_shortage = next(list_getter)
    graphs = [graph_holding, graph_shortage, graph_fixed]

    cost_s = 0.1
    cost_f = 1
    cost_h = 4.9

    all_x = collect_x(graph_fixed, graph_holding, graph_shortage)
    for graph in graphs:
        for x in all_x:
            generate(graph, x)
    combined_graph = []
    for f, h, s in zip(*graphs):
        if not f[0] == s[0] == h[0]:
            print("WARNING: x values not alligned")
        combined_graph.append((x_val(f), cost_f*y_val(f) + cost_h*y_val(h) + cost_s*y_val(s)))
    pass


def collect_x(l1, l2, l3):
    xs = []
    for i in l1:
        xs.append(x_val(i))
    for i in l2:
        xs.append(x_val(i))
    for i in l3:
        xs.append(x_val(i))
    xs = list(set(xs))  # remove duplicates
    xs.sort()
    return xs


def generate(graph, x):
    new_y = 0
    i = find_interval(graph, x)
    if i == -1:
        return
    if 0 < i < len(graph):
        slope = find_slope(graph[i - 1], graph[i])
    if i == 0:
        slope = find_slope(graph[i], graph[i + 1])
    if i == len(graph):
        slope = find_slope(graph[i - 2], graph[i - 1])
    if i < len(graph):
        new_y = y_val(graph[i]) + x_dif(graph[i], (x, 0)) * slope
    else:  # todo
        new_y = y_val(graph[i-1]) + x_dif(graph[i-1], (x, 0)) * slope
    graph.insert(i, (x, new_y))


def find_slope(p1, p2):
    y_dif = y_val(p2) - y_val(p1)
    x_dif = x_val(p2) - x_val(p1)

    return y_dif / x_dif


def find_interval(graph, x):
    for num, elem in enumerate(graph):
        if x == x_val(elem):
            return -1
        if x < x_val(elem):
            return num
    return len(graph)


def x_val(elem):
    return elem[0]


def y_val(elem):
    return elem[1]


def x_dif(p1, p2):
    return x_val(p2) - x_val(p1)


combine()
