#!/usr/bin/env python

import datetime
import datagram
from network import Link, Route
import select
import signal
import socket
import sys

def advertise(signum, frame):
    advertisement = datagram.pack(local_addr, local_port, "UPDATE", routes)
    for link in neighbors:
        neighbors[link].send(advertisement)

if __name__ == "__main__":

    if len(sys.argv) < 6 or len(sys.argv) % 3 != 0:
        exit("usage: ./bfclient.py localport timeout [ipaddress1 port1 weight1 ...]")

    local_addr = socket.gethostbyname(socket.gethostname())
    local_port = int(sys.argv[1])
    here = local_addr + ":" + str(local_port)
    timeout = int(sys.argv[2])

    in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    in_sock.bind(("", local_port))

    neighbors = dict()
    routes = dict()
    last_seen = dict()
    neighbor_routes = dict()

    for i in range(3, len(sys.argv), 3):
        if sys.argv[i] == "localhost" or sys.argv[i] == "127.0.0.1":
            new_host = socket.gethostname()
        else:
            new_host = sys.argv[i]
        new_ip = socket.gethostbyname(new_host)
        new_port = sys.argv[i + 1]
        new_distance = sys.argv[i + 2]

        new_link = Link(new_ip, new_port, new_distance)
        new_route = Route(new_ip, new_port, new_distance, new_link)

        neighbors[new_link.id] = new_link
        routes[new_route.id] = new_route
        last_seen[new_route.id] = datetime.datetime.now()
        neighbor_routes[new_route.id] = dict()

    advertise(0,0)
    signal.alarm(timeout)
    signal.signal(signal.SIGALRM, advertise)

    while True:
        try:
            ready, spam, eggs = select.select([in_sock, sys.stdin], [], [], timeout)
            if ready:
                for source in ready:
                    if source is in_sock:
                        received, ham = source.recvfrom(4096)
                        recv_source, recv_time, command, data = datagram.unpack(received)
                        if command == "UPDATE" and recv_time > last_seen[recv_source]:
                            last_seen[recv_source] = datetime.datetime.now()
                            neighbor_routes[recv_source] = datagram.dictionary(data)
                            for destination in neighbor_routes[recv_source]:
                                if destination != here:
                                    if destination not in routes:
                                        new_ip, colon, new_port = destination.partition(":")
                                        routes[destination] = Route(new_ip, new_port,
                                                                    neighbor_routes[recv_source][destination] + neighbors[recv_source].distance,
                                                                    neighbors[recv_source])
                                        advertise(0,0)
                                        signal.alarm(timeout)
                                    elif routes[destination] > neighbor_routes[recv_source][destination] + neighbors[recv_source].distance:
                                        routes[destination].distance = neighbor_routes[recv_source][destination] + neighbors[recv_source].distance
                                        routes[destination].link = neighbors[recv_source]
                                        advertise(0,0)
                                        signal.alarm(timeout)
                    else:
                        # handle new command
                        pass
        except select.error:
            advertise(0,0)

        print "Routing table:"
        for row in routes:
            print routes[row]