import socket


class Destination:
    def __init__(self, ip_address, port, distance):
        self.ip_address = socket.gethostbyname(ip_address)
        self.port = int(port)
        self.id = self.ip_address + ":" + str(port)
        self.distance = int(distance)


class Link(Destination):
    def __init__(self, ip_address, port, distance):
        Destination.__init__(self, ip_address, port, distance)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        self.socket.sendto(data, (self.ip_address, self.port))

    def __str__(self):
        return "(" + self.ip_address + ":" + str(self.port) + ")"

class Route(Destination):
    def __init__(self, ip_address, port, distance, link):
        Destination.__init__(self, ip_address, port, distance)
        self.link = link

    def __str__(self):
        return "Destination = " + self.ip_address + ":" + str(self.port) +\
            ", Cost = " + str(self.distance) + ", " + str(self.link)