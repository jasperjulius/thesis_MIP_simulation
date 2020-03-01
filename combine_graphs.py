# -------------------------------------------------------------------------------
# used to combine multiple piecewise linear objective functions into one
#   implemented to lower run time
# -------------------------------------------------------------------------------

from math import trunc
from math import ceil


def combine(g1, c1, g2, c2, g3, c3):
    graphs = [g1, g2, g3]

    all_x = collect_x(graphs)
    for graph in graphs:
        for x in all_x:
            generate_point(graph, x)
    combined_graph = []
    for p1, p2, p3 in zip(*graphs):
        if not p1[0] == p2[0] == p3[0]:
            print("WARNING: mip - combine - x values not alligned")
        combined_graph.append((x_val(p1), c1 * y_val(p1) + c2 * y_val(p2) + c3 * y_val(p3)))
    return combined_graph


def combine_2(g1, c1, g2, c2):
    graphs = [g1, g2]

    all_x = collect_x(graphs)

    for graph in graphs:
        for x in all_x:
            generate_point(graph, x)
    combined_graph = []
    for p1, p2 in zip(*graphs):
        if not p1[0] == p2[0]:
            print("WARNING: mip - combine - x values not alligned")
        combined_graph.append((x_val(p1), c1 * y_val(p1) + c2 * y_val(p2)))
    return combined_graph


def collect_x(graphs):
    xs = []
    for g in graphs:
        for i in g:
            xs.append(x_val(i))
    xs = list(set(xs))  # remove duplicates
    xs.sort()
    return xs


def transfer_to_Qs(graph, q):
    result = []
    lb = calc_lb(x_val(graph[0]), q)

    for old_x in range(lb, x_val(graph[-1]) + q, q):
        generate_point(graph, old_x)
    graph = [i for i in graph if x_val(i) % q == 0]
    for i in graph:
        result.append((x_val(i) / q, y_val(i)))
    return result


def calc_lb(x, q):
    if x >= 0:
        return 0
    if x % q == 0:
        return x
    return -ceil((-x)/q)*q

def generate_point(graph, x):
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
    else:
        new_y = y_val(graph[i - 1]) + x_dif(graph[i - 1], (x, 0)) * slope
    graph.insert(i, (x, new_y))


def find_slope(p1, p2):
    y_dif = y_val(p2) - y_val(p1)
    x_dif = x_val(p2) - x_val(p1)
    if x_dif == 0:
        print("get rekt")
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
