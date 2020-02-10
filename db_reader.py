import shelve

name = "process0 - lets go"
name_header = name +" - header"

db_header = shelve.open(name_header)
for i in db_header.keys():
    print(i, db_header[i])
db_header.close()

db_data = shelve.open(name)


def mip(elem):
    return elem[1][0]


list = []
for k in db_data.keys():
    list.append((k, db_data[k]))
list.sort(key=mip)
for i in list:
    print(i)
db_data.close()
