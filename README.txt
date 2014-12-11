bfclient.py

BFClient.py is a script that may be used to simulate a network of nodes. It uses the bellman-ford algorithm to find the optimal route and find new ones if there's a link change. It works with a dynamic network, capable of having nodes enter and exit, and in a variety of configurations.

The program may be invoked via command line using the structure "./bfclient.py localport timeout [ipaddress1 port1 weight1 ...]", with as many links as necessary between the brackets.

Once started, the program starts a command prompt. The user may use the following commands:

SHOWLINKS:
Displays working links to nearby nodes

SHOWRT:
Displays routing table

LINKDOWN <ip_address> <port>:
Simulates link failure on the link to <ip_address>:<port>

LINKUP <ip_address> <port>:
Restores a previously LINKDOWNed link at the input address.

CLOSE:
Closes the host, shutting down the program.

Messages are exchanged between links using the following plaintext structure:

<source_ip>:<source:port>
<time>
<command>
<data>
END

time is in the format YYYY:MM:DD HH:MM:SS.mmmmmmm, and data is empty for all commands except UPDATE. Commands available are UPDATE, LINKDOWN, and LINKUP. 
In UPDATE, data contains the routing table for the source host, with each row in the form "<destination_ip>:<destination_port> <cost>".

The program works well, but has expected bugs in certain situations involving loops that count to infinity.