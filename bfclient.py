#!/usr/bin/env python

import datetime
import datagram
from network import Link, Route
import select
import signal
import socket
import sys


# Function to prompt the user for a new command
def prompt():
    sys.stdout.write("> ")
    sys.stdout.flush()


# Function to exit gracefully
def quit(signum, frame):
    print  # New line after ^C
    exit(0)


# Advertises routing table to other nodes
def advertise(signum, frame):
    advertisement = datagram.pack(here, "UPDATE", routes)
    for link in neighbors:
        if neighbors[link].distance < float("inf"):
            neighbors[link].send(advertisement)
    signal.alarm(timeout) # timeout handled by alarm.
                          # This way user input won't reset the timeout.
    signal.signal(signal.SIGALRM, advertise)


# Main method
if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)

    # Handle command line args
    if len(sys.argv) < 6 or len(sys.argv) % 3 != 0:
        exit("usage: ./bfclient.py localport timeout [ipaddress1 port1 weight1 ...]")
    local_addr = socket.gethostbyname(socket.gethostname())
    local_port = int(sys.argv[1])
    here = local_addr + ":" + str(local_port)
    timeout = int(sys.argv[2])

    # Prepare receiving socket
    in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    in_sock.bind(("", local_port))

    # Prepare data structures
    neighbors = dict()  # Neighboring links
    original_links = dict()  # Store original distances for LINKUP
    routes = dict()  # Routing table
    last_seen = dict()  # To keep track of recent activity

    for i in range(3, len(sys.argv), 3):
        # Resolves inconsistencies across routing tables
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

                    # Handle new messages
                    if source is in_sock:

                        # I decided not to use the address returned by recvfrom.
                        # I feel like that's cheating, in the network layer
                        received, ham = source.recvfrom(4096)
                        messages = filter(bool, received.split("END\n"))
                        for message in messages:
                            recv_source, recv_time, command, data = datagram.unpack(message)

                            # Disregard out-of-order packets
                            if recv_source not in last_seen or last_seen[recv_source] < recv_time:
                                last_seen[recv_source] = datetime.datetime.now()

                                # ROUTE UPDATE
                                if command == "UPDATE":
                                    neighbor_table = datagram.dictionary(data)
                                    for destination in neighbor_table:

                                        # Refers to current link
                                        if destination == here:

                                            # New link
                                            if recv_source not in neighbors:
                                                new_link = Link(recv_source, neighbor_table[destination])
                                                neighbors[recv_source] = new_link
                                                original_links[recv_source] = new_link.distance

                                                if recv_source not in routes:
                                                    new_route = Route(recv_source, neighbor_table[destination],
                                                                  neighbors[recv_source])
                                                    routes[recv_source] = new_route

                                            # Link change (always assume received version is right)
                                            if neighbor_table[destination] != neighbors[recv_source].distance:
                                                diff = neighbor_table[destination] - neighbors[recv_source].distance
                                                neighbors[recv_source].distance += diff
                                                for host in routes:
                                                    if routes[host].link.id == recv_source:
                                                        routes[recv_source].distance += neighbor_table[destination]

                                        else:
                                            total_distance = neighbors[recv_source].distance + neighbor_table[destination]

                                            # New route
                                            if destination not in routes:
                                                new_route = Route(destination,
                                                                  neighbor_table[destination] + neighbors[
                                                                      recv_source].distance,
                                                                  neighbors[recv_source])
                                                routes[destination] = new_route
                                                advertise(0, 0)

                                            # Better route, or change in current one
                                            elif routes[destination].link.id == recv_source and routes[destination].distance != total_distance \
                                                    or routes[destination].distance > total_distance:
                                                routes[destination].distance = total_distance
                                                routes[destination].link = neighbors[recv_source]
                                                advertise(0, 0)

                                elif command == "LINKDOWN":
                                    neighbors[recv_source].distance = float("inf")
                                    for destination in routes:
                                        if routes[destination].link.id == recv_source:
                                            routes[destination].distance = float("inf")
                                    advertise(0, 0)
                                elif command == "LINKUP":
                                    neighbors[recv_source].distance = original_links[recv_source]
                                    routes[recv_source].distance = original_links[recv_source]
                                    for i in routes:
                                        print i + " -> " + str(routes[i].distance)
                                    advertise(0, 0)

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
                                down_message = datagram.pack(here, "LINKDOWN")
                                neighbors[down_id].send(down_message)
                                neighbors[down_id].distance = float("inf")
                                last_seen[down_id] = datetime.datetime.now()
                                for destination in routes:
                                    if routes[destination].link.id == down_id:
                                        routes[destination].distance = float("inf")
                                advertise(0, 0)

                            except IndexError:
                                print("ERROR: command format incorrect.")
                            except KeyError:
                                print("ERROR: link does not exist.")
                        elif command == "LINKUP":
                            try:
                                if args[1] == "localhost" or args[1] == "127.0.0.1":
                                    up_addr = socket.gethostname()
                                else:
                                    up_addr = args[1]
                                up_id = socket.gethostbyname(up_addr) + ":" + args[2]
                                up_message = datagram.pack(here, "LINKUP")
                                neighbors[up_id].send(up_message)
                                neighbors[up_id].distance = original_links[up_id]
                                routes[up_id].distance = original_links[up_id]
                                last_seen[up_id] = datetime.datetime.now()
                                advertise(0, 0)

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
            # If timeout happens while select is waiting
            advertise(0, 0)

        for host in last_seen:
            time_since = datetime.datetime.now() - last_seen[host]
            if time_since.total_seconds() > 3 * timeout:
                if host in neighbors:
                    neighbors[host].distance = sys.maxint
                    routes[host].distance = sys.maxint