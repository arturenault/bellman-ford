#!/usr/bin/env python

import datagram
from network import Link, Route
import socket
import sys

if __name__ == "__main__":

    if len(sys.argv) < 6 or len(sys.argv) % 3 != 0:
        exit("usage: ./bfclient.py localport timeout [ipaddress1 port1 weight1 ...]")

    local_addr = socket.gethostbyname(socket.gethostname())
    local_port = int(sys.argv[1])
    timeout = int(sys.argv[2])

    in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    in_sock.bind(("", local_port))

    neighbors = []
    routes = dict()
    neighbor_routes = dict()

    for i in range(3, len(sys.argv), 3):
        new_ip = sys.argv[i]
        new_port = sys.argv[i + 1]
        new_distance = sys.argv[i + 2]

        new_link = Link(new_ip, new_port, new_distance)
        new_route = Route(new_ip, new_port, new_distance, new_link)

        neighbors.append(new_link)
        routes[new_route.id] = new_route
        neighbor_routes[new_route.id] = dict()

    advertisement = datagram.pack(local_addr, local_port, "UPDATE", routes)
    for neighbor in neighbors:
        neighbor.send(advertisement)