import socket
import sys


class Destination:
    def __init__(self, address, distance):
        self.ip_address, colon, port_string = address.partition(":")
        self.port = int(port_string)
        self.id = address
        self.distance = int(distance)


class Link(Destination):
    def __init__(self, address, distance):
        Destination.__init__(self, address, distance)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        self.socket.sendto(data, (self.ip_address, self.port))

    def __str__(self):
        return "(" + self.ip_address + ":" + str(self.port) + ")"


class Route(Destination):
    def __init__(self, address, distance, link):
        Destination.__init__(self, address, distance)
        self.link = link

    def __str__(self):
        if self.distance == sys.maxint:
            dist_string = "Infinity"
        else:
            dist_string = str(self.distance)
        return "Destination = " + self.ip_address + ":" + str(self.port) + \
               ", Cost = " + dist_string + ", " + str(self.link)