import shelve

name = "test db"
name_header = name + " - header"

db_header = shelve.open(name_header)
for i in db_header.keys():
    print(i, db_header[i])
periods = db_header["periods"]
db_header.close()


def mip(elem):
    return elem[1][0]


def batch(elem):
    return elem[1][1]


def fifo(elem):
    return elem[1][2]


def key(elem):
    return elem[0]


def value(elem):
    return elem[1]


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
    for i in dict.keys():
        for j in range(len(dict[i])):
            dict[i][j] = sorted(dict[i][j])
        print(i, dict[i],"\n")
    return dict


db_data = shelve.open(name)
db_list = []
for k in db_data.keys():
    db_list.append((k, db_data[k]))

db_list.sort(key=lambda x: x[0])
db_list.sort(key=mip)

db_data.close()

group(db_list)

print(min(db_list, key=mip), min(db_list, key=batch), min(db_list, key=fifo))
print("MIN: ", round(mip(min(db_list, key=mip)) / periods, 2), round(batch(min(db_list, key=batch)) / periods, 2),
      round(fifo(min(db_list, key=fifo)) / periods, 2))
