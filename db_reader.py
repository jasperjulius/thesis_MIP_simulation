# -------------------------------------------------------------------------------
# used to analyse generated results, reading, sorting and filtering the data
# -------------------------------------------------------------------------------

import shelve
import pickle

def mip(elem):
    return elem[1][0]


def batch(elem):
    return elem[1][1]


def fcfs(elem):
    return elem[1][2]


def key(elem):
    return elem[0]


def value(elem):
    return str(elem[1])


def group(db_list):
    def concatenate(old, new):
        new_elems = new.split(sep=", ")
        for i in range(len(old)):
            old[i].add(new_elems[i])
        return old

    dict = {}
    for i in db_list:
        if value(i) in dict:
            old_val = dict.get(value(i))
            new_val = key(i)
            dict[value(i)] = concatenate(old_val, new_val)

        else:
            dict[value(i)] = [{i} for i in key(i).split(sep=", ")]
    for num, i in enumerate(dict.keys()):
        for j in range(len(dict[i])):
            dict[i][j] = sorted(dict[i][j])
        if num < 30:
            pass
            # print(dict[i], "\n\t\t", i, "\n")
    return dict


def run(name, fifo):
    db_header = shelve.open(name + " - header")
    for k in db_header.keys():
        print(k, ": ", db_header[k])
    periods = db_header["periods"]
    db_header.close()
    db_data = shelve.open(name)
    db_list = []
    for k in db_data.keys():
        db_list.append((k, db_data[k]))

    # db_list.sort(key=lambda x: x[0])
    if fifo:
        db_list.sort(key=mip)
    else:
        db_list.sort(key=mip)
    db_data.close()

    group(db_list)
    if fifo:
        print((min(db_list, key=mip)))
        print("MIN: ", round(mip(min(db_list, key=lambda x: x[1][0][0]))[0] / periods, 2))
    else:
        print(min(db_list, key=mip), "\n", min(db_list, key=batch), "\n", min(db_list, key=fcfs))
        print("MIN: ", round(mip(min(db_list, key=mip)) / periods, 4),
            round(batch(min(db_list, key=batch)) / periods, 4),
            round(fcfs(min(db_list, key=fcfs)) / periods, 4))


def diffs_batch_mip(name):
    db = shelve.open(name)
    for k in db.keys():
        if not db[k][1] == db[k][2]:
            print(k, ": ", db[k])
    db.close()

if __name__ == "__main__":
    with open("scenario_names.txt", "rb") as f:
        all_names = pickle.load(f)
    for name in all_names:
        run(name, False)
        print("")
        print("")
        print("")
