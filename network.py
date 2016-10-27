
# This file contains all the classes and methods for the basic network architecture




class Host(object):
    """docstring for Host."""
    def __init__(self, id):
        super(Host, self).__init__()
        self.id = id


class Router(object):
    """docstring for Router."""
    def __init__(self, routing_table):
        super(Router, self).__init__()
        self.routing_table = routing_table


class Link(object):
    """docstring for Link."""
    def __init__(self, start_node, end_node, buffer_size, capacity, delay):
        super(Link, self).__init__()
        self.start_node = start_node
        self.end_node = end_node
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
    def __init__(self, source_host, destination_host, congestion_control_algorithm):
        super(Flow, self).__init__()
        self.source_host = source_host
        self.destination_host = destination_host
        self.unacknowledged_packets = set()

    def congestion_control_algorithm(self):
        pass
