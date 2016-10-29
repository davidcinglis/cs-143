
import heapq



# This file contains all the classes and methods for the basic network architecture


class Network(object):
    """docstring for Network."""

    def __init__(self):
        super(Network, self).__init__()
        self.node_dict = dict()
        self.link_dict = dict()
        self.flow_list = dict()

        self.event_queue = []
        self.event_dict = {}



    def add_host(self, node_id):
        self.node_dict[node_id] = Host(node_id)

    def add_router(self, node_id):
        self.node_dict[node_id] = Router(node_id)

    def add_link(self, link_id, node_1, node_2, buffer_size, capacity, delay):
        self.link_dict[link_id] = Link(link_id, node_1, node_2, buffer_size, capacity, delay)

    def add_flow(self, flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm):
        self.flow_dict[flow_id] = Flow(flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm)





class Event(object):
    """docstring for Event."""
    def __init__(self, timestamp, handler):
        super(Event, self).__init__()
        self.timestamp = timestamp
        self.handler = handler

    def __cmp__(self, other):
        return self.timestamp - other.timestamp


class Host(object):
    """docstring for Host."""
    def __init__(self, node_id):
        super(Host, self).__init__()
        self.node_id = node_id


class Router(object):
    """docstring for Router."""
    def __init__(self, id):
        super(Router, self).__init__()
        self.node_id = node_id
        # self.routing_table = routing_table


class Link(object):
    """docstring for Link."""
    def __init__(self, link_id, node_1, node_2, buffer_size, capacity, delay):
        super(Link, self).__init__()
        self.link_id = link_id
        self.node_1 = node_1
        self.node_2 = node_2
        self.most_recent_transmitting_node = None
        self.buffer_size = buffer_size
        self.capacity = capacity
        self.delay = delay


class Packet(object):
    """docstring for Packet."""
    def __init__(self, source, destination):
        super(Packet, self).__init__()
        self.payload_size = payload_size
        self.source = source
        self.destination = destination
        self.unique_packet_id



class DataPacket(Packet):
    """docstring for DataPacket."""
    def __init__(self):
        super(DataPacket, self).__init__()
        self.size = 1024 * 8 # All data packets have 1024 bytes


class AcknowledgementPacket(Packet):
    """docstring for AcknowledgementPacket."""
    def __init__(self):
        super(AcknowledgementPacket, self).__init__()
        self.size = 64 * 8 # All acknowledgement packets have 64 bytes.





class Flow(object):
    """docstring for Flow."""
    def __init__(self, flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm):
        super(Flow, self).__init__()
        self.flow_id
        self.source_host = source_host
        self.destination_host = destination_host

        self.payload_size = payload_size
        self.start_time = start_time
        self.unacknowledged_packets = set()

    def congestion_control_algorithm(self):
        return True
