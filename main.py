

from network import *


def run_test_case_0_lite():

    n = Network()

    h1 = Host("h1")
    h2 = Host("h2")

    n.add_host(h1)
    n.add_host(h2)

    # Adds link l1 from h1 to h2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l1", h1, h2, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds flow f1 from h1 to h2. Flow has payload 3 packets, starts at t=1, no congestion control.
    n.add_flow("f1", h1, h2, DATA_PACKET_SIZE * 3, 1, None)


    # setup the routing table for h1
    h1.routing_table["h2"] = n.link_dict["l1"]

    # setup the routing table for h2
    h2.routing_table["h1"] = n.link_dict["l1"]

    n.event_loop()


def run_test_case_0():

    n = Network()

    h1 = Host("h1")
    h2 = Host("h2")

    n.add_host(h1)
    n.add_host(h2)

    # Adds link l1 from h1 to h2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l1", h1, h2, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds flow f1 from h1 to h2. Flow has payload 20MB, starts at t=1, no congestion control.
    n.add_flow("f1", h1, h2, 20 * 10**6 * 8, 1, None)


    # setup the routing table for h1
    h1.routing_table["h2"] = n.link_dict["l1"]

    # setup the routing table for h2
    h2.routing_table["h1"] = n.link_dict["l1"]

    n.event_loop()


def run_test_case_1():

    n = Network()

    h1 = Host("h1")
    h2 = Host("h2")

    r1 = Router("r1")
    r2 = Router("r2")
    r3 = Router("r3")
    r4 = Router("r4")

    n.add_host(h1)
    n.add_host(h2)

    n.add_router(r1)
    n.add_router(r2)
    n.add_router(r3)
    n.add_router(r4)



    # Adds link l0 from h1 to r2. Link has buffer 64 KB, 12.5 Mbps capacity, 10 ms delay
    n.add_link("l0", n.node_dict["h1"], n.node_dict["r1"], 64 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    # Adds link l1 from r1 to r2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l1", n.node_dict["r1"], n.node_dict["r2"], 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l2 from r1 to r3. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l2", n.node_dict["r1"], n.node_dict["r3"], 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l3 from r2 to r4. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l3", n.node_dict["r2"], n.node_dict["r4"], 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l4 from r3 to r4. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l4", n.node_dict["r3"], n.node_dict["r4"], 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l5 from r4 to h2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l5", n.node_dict["r4"], n.node_dict["h2"], 64 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)


    # Adds flow f1 from h1 to h2. Flow has payload 20MB, starts at t=0.5, no congestion control.
    n.add_flow("f1", n.node_dict["h1"], n.node_dict["h2"], 20 * 10**6 * 8, 0.5, None)


    # setup the routing table for h1
    n.node_dict["h1"].routing_table["h2"] = n.link_dict["l0"]

    # setup the routing table for h2
    n.node_dict["h2"].routing_table["h1"] = n.link_dict["l5"]

    # Setup the routing tables for the routers


    n.event_loop()





if __name__ == '__main__':
    run_test_case_0_lite()
