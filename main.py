

from network import *
from logging import *


def run_test_case_0_lite():

    n = Network()

    h1 = Host("h1")
    h2 = Host("h2")

    n.add_node(h1)
    n.add_node(h2)

    # Adds link l1 from h1 to h2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l1", h1, h2, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds flow f1 from h1 to h2. Flow has payload 5000 packets, starts at t=1, no congestion control.
    n.add_flow("f1", h1, h2, DATA_PACKET_SIZE * 500, 1, None)


    # setup the routing table for h1
    h1.routing_table["h2"] = n.link_dict["l1"]

    # setup the routing table for h2
    h2.routing_table["h1"] = n.link_dict["l1"]

    n.event_loop()

    for flow in n.flow_dict:
        plot_window_size(n.flow_dict[flow])
        #plot_flow_rate(n.flow_dict[flow])
        #plot_round_trip_time(n.flow_dict[flow])

    for link in n.link_dict:
        plot_buffer_occupancy(n.link_dict[link])
        plot_packet_loss(n.link_dict[link])
        plot_link_rate(n.link_dict[link])



def run_test_case_0():

    n = Network()

    h1 = Host("h1")
    h2 = Host("h2")

    n.add_node(h1)
    n.add_node(h2)

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

    n.add_node(h1)
    n.add_node(h2)

    n.add_node(r1)
    n.add_node(r2)
    n.add_node(r3)
    n.add_node(r4)



    # Adds link l0 from h1 to r2. Link has buffer 64 KB, 12.5 Mbps capacity, 10 ms delay
    n.add_link("l0", h1, r1, 64 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    # Adds link l1 from r1 to r2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l1", r1, r2, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l2 from r1 to r3. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l2", r1, r3, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l3 from r2 to r4. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l3", r2, r4, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l4 from r3 to r4. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l4", r3, r4, 64 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    # Adds link l5 from r4 to h2. Link has buffer 64 KB, 10 Mbps capacity, 10 ms delay
    n.add_link("l5", r4, h2, 64 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)


    # Adds flow f1 from h1 to h2. Flow has payload 20MB, starts at t=0.5, no congestion control.
    n.add_flow("f1", h1, h2, DATA_PACKET_SIZE * 5000, 0.5, "reno")
    # n.add_flow("f1", h1, h2, 20 * 10**6 * 8, 0.5, None)


    # setup the routing table for h1
    h1.routing_table["h2"] = n.link_dict["l0"]

    # setup the routing table for h2
    h2.routing_table["h1"] = n.link_dict["l5"]

    # Setup the routing tables for r1
    r1.routing_table["h1"] = n.link_dict["l0"]
    r1.routing_table["h2"] = n.link_dict["l1"]

    # Setup the routing tables for r2
    r2.routing_table["h1"] = n.link_dict["l1"]
    r2.routing_table["h2"] = n.link_dict["l3"]

    # Setup the routing tables for r3
    r3.routing_table["h1"] = n.link_dict["l2"]
    r3.routing_table["h2"] = n.link_dict["l4"]

    # Setup the routing tables for r4
    r4.routing_table["h1"] = n.link_dict["l4"]
    r4.routing_table["h2"] = n.link_dict["l5"]

    n.event_loop()

    for flow in n.flow_dict:
        plot_flow_rate(n.flow_dict[flow])
        plot_window_size(n.flow_dict[flow])
        #plot_round_trip_time(n.flow_dict[flow])
    #
    for link in n.link_dict:
        plot_packet_loss(n.link_dict[link])
        plot_link_rate(n.link_dict[link])



def run_test_case_2():

    n = Network()

    s1 = Host("s1")
    s2 = Host("s2")
    s3 = Host("s3")
    t1 = Host("t1")
    t2 = Host("t2")
    t3 = Host("t3")

    r1 = Router("r1")
    r2 = Router("r2")
    r3 = Router("r3")
    r4 = Router("r4")

    n.add_node(s1)
    n.add_node(s2)
    n.add_node(s3)
    n.add_node(t1)
    n.add_node(t2)
    n.add_node(t3)

    n.add_node(r1)
    n.add_node(r2)
    n.add_node(r3)
    n.add_node(r4)



    n.add_link("l0", r1, s2, 128 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    n.add_link("l1", r1, r2, 128 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    n.add_link("l2", r2, r3, 128 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    n.add_link("l3", r3, r4, 128 * 1000 * 8, 10 * 10**6, 10 * 10**-3)
    n.add_link("l4", r1, s1, 128 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    n.add_link("l5", t2, r2, 128 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    n.add_link("l6", s3, r3, 128 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    n.add_link("l7", t1, r4, 128 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)
    n.add_link("l8", r4, t3, 128 * 1000 * 8, 12.5 * 10**6, 10 * 10**-3)


    # Adds flow f1. Flow has payload 35MB, starts at t=0.5, no congestion control.
    n.add_flow("f1", s1, t1, DATA_PACKET_SIZE * 5000, 0.5, "reno")

    # Adds flow f2. Flow has payload 15MB, starts at t=10, no congestion control.
    n.add_flow("f2", s2, t2, DATA_PACKET_SIZE * 5000, 0.5, "reno")

    # Adds flow f3. Flow has payload 30MB, starts at t=20, no congestion control.
    n.add_flow("f3", s3, t3, DATA_PACKET_SIZE * 5000, 0.5, "reno")



    # Setup the routing tables for the routers


    n.event_loop()

    for flow in n.flow_dict:
        plot_flow_rate(n.flow_dict[flow])
        plot_window_size(n.flow_dict[flow])
        #plot_round_trip_time(n.flow_dict[flow])

    for link in n.link_dict:
        plot_packet_loss(n.link_dict[link])
        plot_link_rate(n.link_dict[link])




if __name__ == '__main__':
    run_test_case_1()
