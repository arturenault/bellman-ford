import datetime


def pack(destination, command, table=None):
    message = destination + "\n" + \
              str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')) + "\n" + \
              command + "\n"
    if table:
        for row in table:
            message += row + " " + str(table[row].distance) + "\n"
    return message + "END\n"


def unpack(message):
    contents = message.split("\n", 3)
    source = contents[0]
    time = datetime.datetime.strptime(contents[1], '%Y-%m-%d %H:%M:%S.%f')
    command = contents[2]
    data = contents[3]
    return source, time, command, data


def dictionary(text):
    distances = dict()
    links = dict()
    for line in text.splitlines():
        array = line.split(" ")
        distances[array[0]] = float(array[1])
    return distances