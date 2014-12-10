#!/usr/bin/env python

import datetime
import datagram
from network import Link, Route
import select
import signal
import socket
import sys


def prompt():
    sys.stdout.write("> ")
    sys.stdout.flush()


def quit(signum, frame):
    print
    exit(0)


def advertise(signum, frame):
    advertisement = datagram.pack(here, "UPDATE", routes)
    for link in neighbors:
        neighbors[link].send(advertisement)
    signal.alarm(timeout)
    signal.signal(signal.SIGALRM, advertise)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)

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
    original_links = dict()
    routes = dict()
    last_seen = dict()

    for i in range(3, len(sys.argv), 3):
        if sys.argv[i] == "localhost" or sys.argv[i] == "127.0.0.1":
            new_host = socket.gethostname()
        else:
            new_host = sys.argv[i]
        new_ip = socket.gethostbyname(new_host)
        new_port = sys.argv[i + 1]
        new_distance = sys.argv[i + 2]
        new_addr = new_ip + ":" + new_port

        new_link = Link(new_addr, new_distance)
        new_route = Route(new_addr, new_distance, new_link)

        neighbors[new_link.id] = new_link
        original_links[new_addr] = new_link.distance
        routes[new_route.id] = new_route
        last_seen[new_route.id] = datetime.datetime.now()


    advertise(0, 0)

    prompt()
    while True:
        try:
            ready, spam, eggs = select.select([in_sock, sys.stdin], [], [], timeout)
            if ready:
                for source in ready:
                    if source is in_sock:
                        received, ham = source.recvfrom(4096)
                        recv_source, recv_time, command, data = datagram.unpack(received)
                        if recv_source not in last_seen or recv_time > last_seen[recv_source]:
                            last_seen[recv_source] = datetime.datetime.now()
                            if command == "UPDATE":
                                neighbor_table = datagram.dictionary(data)
                                for destination in neighbor_table:
                                    if destination == here:
                                        if recv_source not in neighbors:
                                            new_link = Link(recv_source, neighbor_table[destination])
                                            neighbors[recv_source] = new_link
                                            original_links[recv_source] = new_link.distance

                                        if recv_source not in routes:
                                            new_route = Route(recv_source, neighbor_table[destination],
                                                              neighbors[recv_source])
                                            routes[recv_source] = new_route

                                        elif neighbor_table[destination] != routes[recv_source].distance:
                                            routes[recv_source].distance = neighbor_table[destination]
                                            routes[recv_source].link = neighbors[recv_source]

                                    else:
                                        if destination not in routes:
                                            routes[destination] = Route(destination,
                                                                        neighbor_table[destination] + neighbors[
                                                                            recv_source].distance,
                                                                        neighbors[recv_source])
                                            advertise(0, 0)
                                        elif routes[destination].link is neighbors[recv_source] and routes[
                                            destination].distance != neighbor_table[destination] \
                                                or routes[destination] > neighbor_table[destination] + neighbors[
                                                    recv_source].distance:
                                            routes[destination].distance = neighbor_table[destination] + neighbors[
                                                recv_source].distance
                                            routes[destination].link = neighbors[recv_source]
                                            advertise(0, 0)
                            elif command == "LINKDOWN":
                                neighbors[recv_source].distance = sys.maxint
                                for destination in routes:
                                    if routes[destination].link.id == down_id:
                                        routes[destination].distance = sys.maxint
                                advertise(0,0)
                            elif command =="LINKUP":
                                neighbors[recv_source].distance = original_links[recv_source].distance
                                routes[recv_source].distance = original_links[recv_source].distance


                    else:
                        args = sys.stdin.readline().strip().split(" ")
                        command = args[0].upper()
                        if command == "SHOWRT":
                            for row in routes:
                                print(routes[row])
                        elif command == "LINKDOWN":
                            try:
                                if args[1] == "localhost" or args[1] == "127.0.0.1":
                                    down_addr = socket.gethostname()
                                else:
                                    down_addr = args[1]
                                down_id = socket.gethostbyname(down_addr) + ":" + args[2]
                                down_message = datagram.pack(down_id, "LINKDOWN")
                                neighbors[down_id].distance = sys.maxint
                                last_seen[down_id] = datetime.datetime.now()
                                for destination in routes:
                                    if routes[destination].link.id == down_id:
                                        routes[destination].distance = sys.maxint
                                advertise(0,0)

                            except IndexError:
                                print("ERROR: command format incorrect.")
                            except KeyError:
                                print("ERROR: link does not exist.")
                        elif command == "LINKUP":
                            try:
                                up_id = args[1] + ":" + args[2]
                                neighbors[up_id].distance = original_links[up_id]
                            except IndexError:
                                print("ERROR: command format incorrect.")
                            except KeyError:
                                print("ERROR: link does not exist.")
                        elif command == "CLOSE":
                            quit(0, 0)
                        else:
                            print("ERROR: unrecognized command.")
                        prompt()

        except select.error:
            advertise(0, 0)

        for host in last_seen:
            time_since = datetime.datetime.now() - last_seen[host]
            if time_since.total_seconds() > 3 * timeout:
                if host in neighbors:
                    neighbors[host].distance = sys.maxint
                    routes[host].distance = sys.maxint