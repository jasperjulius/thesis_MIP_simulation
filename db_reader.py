import shelve

name = "process0 - low var"
name_header = name +" - header"

db_header = shelve.open(name_header)
for i in db_header.keys():
    print(i, db_header[i])
periods = db_header["periods"]
db_header.close()

db_data = shelve.open(name)


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

def group(list):
    result = []

list = []
for k in db_data.keys():
    list.append((k, db_data[k]))

list.sort(key=lambda x: x[0])
list.sort(key=mip)
for i in list:
    print(i)
db_data.close()

print(min(list, key=mip), min(list, key=batch), min(list, key=fifo))
print("MIN: ", round(mip(min(list, key=mip))/periods, 2), round(batch(min(list, key=batch))/periods, 2), round(fifo(min(list, key=fifo))/periods, 2))
