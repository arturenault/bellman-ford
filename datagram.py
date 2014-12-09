import datetime


def pack(ip, port, command, table=None):
    message = ip + ":" + str(port) + "\n" + \
              str(datetime.datetime.now()) + "\n" + \
              command + "\n"
    for row in table:
        message += row + " " + table[row].distance + "\n"
    print(message)
    return message


def unpack(message):
    contents = message.split("\n", 3)
    source = contents[0]
    time = datetime.strptime(contents[1], '%Y-%m-%d %H:%M:%S.%f')
    command = contents[2]
    data = contents[3]
    return source, time, command, data