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


def group(db_list, extended=False):
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
        if extended:
            print(dict[i], "\n\t\t", i, "\n")
        if num < 30:
            pass
            # print(dict[i], "\n\t\t", i, "\n")
    return dict


def run(name, extended):
    db_header = shelve.open(name + " - header")
    for k in db_header.keys():
        if extended:
            print(k, ": ", db_header[k])
        elif k == "name":
            print(k, ": ", db_header[k])
    periods = db_header["periods"]
    db_header.close()
    db_data = shelve.open(name)
    db_list = []
    for k in db_data.keys():
        db_list.append((k, db_data[k]))

    # db_list.sort(key=lambda x: x[0])

    db_list.sort(key=mip)
    db_data.close()

    group(db_list, extended=extended)

    min_mip = min(db_list, key=mip)
    min_batch = min(db_list, key=batch)
    min_fcfs = min(db_list, key=fcfs)
    s = str(round(mip(min_mip)/ periods, 3)) + " (" + min_mip[0] + ") & " + str(round(batch(min_batch)/ periods, 3)) + " (" + min_batch[
        0] + ") & " + str(round(fcfs(min_fcfs)/ periods, 3)) + " (" + min_fcfs[0] + ") \\\\"
    print("da mins", s)



def diffs_batch_mip(name):
    db = shelve.open(name)
    for k in db.keys():
        if not db[k][1] == db[k][2]:
            print(k, ": ", db[k])
    db.close()


if __name__ == "__main__":
    # with open("scenario_names.txt", "rb") as f:
    #    all_names = pickle.load(f)
    all_names = ['DIESE, L2-2, high var, high c_s, low h0', 'DIESE L2-2, low var, high c_s, low h0',
                 'DIESE, L2-2, high var, low c_s, low h0', 'DIESE L2-2, low var, low c_s, low h0',
                 'DIESE, L2-2, high var, high c_s, high h0', 'DIESE L2-2, low var, high c_s, high h0',
                 'DIESE, L2-2, high var, low c_s, high h0', 'DIESE L2-2, low var, low c_s, high h0',
                 'DIESE, L1-3, high var, high c_s, low h0', 'DIESE L1-3, low var, high c_s, low h0',
                 'DIESE, L1-3, high var, low c_s, low h0', 'DIESE L1-3, low var, low c_s, low h0',
                 'DIESE, L1-3, high var, high c_s, high h0', 'DIESE L1-3, low var, high c_s, high h0',
                 'DIESE, L1-3, high var, low c_s, high h0', 'DIESE L1-3, low var, low c_s, high h0',
                 'DIESE, L3-1, high var, high c_s, low h0', 'DIESE L3-1, low var, high c_s, low h0',
                 'DIESE, L3-1, high var, low c_s, low h0', 'DIESE L3-1, low var, low c_s, low h0',
                 'DIESE, L3-1, high var, high c_s, high h0', 'DIESE L3-1, low var, high c_s, high h0',
                 'DIESE, L3-1, high var, low c_s, high h0', 'DIESE L3-1, low var, low c_s, high h0']

    all_names = ['ANDERE, L1-3, high var, high c_s, low h0', 'ANDERE L1-3, low var, high c_s, low h0',
                 'ANDERE, L1-3, high var, low c_s, low h0', 'ANDERE L1-3, low var, low c_s, low h0',
                 'ANDERE, L1-3, high var, high c_s, high h0', 'ANDERE L1-3, low var, high c_s, high h0',
                 'ANDERE, L1-3, high var, low c_s, high h0', 'ANDERE L1-3, low var, low c_s, high h0']

    for name in all_names:
        run(name, False)
        print("")
        print("")
        print("")
