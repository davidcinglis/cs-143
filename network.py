
# This file contains all the classes and methods for the basic network architecture
import heapq

DATA_PACKET_SIZE = 1024 * 8
ACK_PACKET_SIZE = 64 * 8
WINDOW_SIZE = 20

class Network(object):
    """docstring for Network."""

    def __init__(self):
        super(Network, self).__init__()
        self.node_dict = dict()
        self.link_dict = dict()
        self.flow_dict = dict()

        self.active_flows = 0

        self.event_queue = EventQueue()

    def add_host(self, node):
        self.node_dict[node.node_id] = node
        node.network = self

    def add_router(self, node):
        self.node_dict[node.node_id] = node
        node.network = self

    def add_link(self, link_id, node_1, node_2, buffer_size, capacity, delay):
        self.link_dict[link_id] = Link(link_id, node_1, node_2, buffer_size, capacity, delay)
        self.link_dict[link_id].network = self

    def add_flow(self, flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm):
        self.flow_dict[flow_id] = Flow(flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm)
        source_host.flow = self.flow_dict[flow_id]
        self.flow_dict[flow_id].network = self

        self.flow_dict[flow_id].setup()

    def event_loop(self):

        self.active_flows = len(self.flow_dict)

        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            event.handle()
            event.print_event_description()

class EventQueue(object):
    def __init__(self):
        self._queue = []

    def push(self, event):
        heapq.heappush(self._queue, (event.timestamp, event))

    def pop(self):
        return heapq.heappop(self._queue)[1]

    def is_empty(self):
        return len(self._queue) == 0



class Event(object):
    """docstring for Event."""
    def __init__(self, timestamp):
        super(Event, self).__init__()
        self.timestamp = timestamp

    def __cmp__(self, other):
        return self.timestamp - other.timestamp


# class AnalyticsEvent(Event):
#     """docstring for AnalyticsEvent."""
#     def __init__(self, timestamp):
#         super(AnalyticsEvent, self).__init__(timestamp)
#         self.arg = arg



class ReceivePacketEvent(Event):
    """docstring for ReceivePacketEvent."""
    def __init__(self, timestamp, packet, receiving_node):
        super(ReceivePacketEvent, self).__init__(timestamp)

        self.packet = packet
        self.receiving_node = receiving_node

    def handle(self):

        if self.packet.destination == self.receiving_node:
            if isinstance(self.packet, DataPacket):
                ack = AcknowledgementPacket(self.packet.packet_id, self.packet.destination, self.packet.source)
                self.receiving_node.network.event_queue.push(ReceivePacketEvent(self.timestamp, ack, self.receiving_node))
            elif isinstance(self.packet, AcknowledgementPacket):
                flow = self.receiving_node.flow
                e = PacketAcknowledgementEvent(self.timestamp, self.packet, flow)
                self.receiving_node.network.event_queue.push(e)
        else:
            next_link = self.receiving_node.routing_table[self.packet.destination.node_id]
            assert isinstance(next_link, Link)
            e = EnterBufferEvent(self.timestamp, self.packet, next_link, self.receiving_node)
            self.receiving_node.network.event_queue.push(e)



    def print_event_description(self):
        print "Timestamp:", self.timestamp, "Receiving packet", self.packet.packet_id, "(", self.packet.source.node_id, "->", self.packet.destination.node_id, ")",  "at node", self.receiving_node.node_id



class EnterBufferEvent(Event):
    """docstring for EnterBufferEvent."""
    def __init__(self, timestamp, packet, link, current_node):
        super(EnterBufferEvent, self).__init__(timestamp)
        self.packet = packet
        self.link = link
        self.current_node = current_node
        if self.link.node_1 == self.current_node:
            self.next_node = self.link.node_2
        elif self.link.node_2 == self.current_node:
            self.next_node = self.link.node_1
        else:
            raise ValueError("Node not in link")


    def handle(self):
        if self.link.available_space - self.packet.size >= 0:
            self.link.available_space -= self.packet.size
            self.link.buffer_occupancy_history.append((self.timestamp, self.link.available_space))

            if self.link.next_send_time == None: # If the buffer is empty
                send_time = self.timestamp
            else:
                send_time = max(self.link.next_send_time, self.timestamp)

            lbe = LeaveBufferEvent(send_time, self.packet, self.link, self.current_node)

            self.link.next_send_time = send_time + float(self.packet.size) / self.link.capacity + self.link.delay

            self.link.network.event_queue.push(lbe)
        else:
            self.link.packets_lost_history.append(self.timestamp)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "Packet", self.packet.packet_id, "(", self.packet.source.node_id, "->", self.packet.destination.node_id, ")", "entering buffer at node", self.current_node.node_id, "(link", self.link.link_id, ")"



class LeaveBufferEvent(Event):
    """docstring for LeaveBufferEvent."""
    def __init__(self, timestamp, packet, link, current_node):
        super(LeaveBufferEvent, self).__init__(timestamp)
        self.packet = packet
        self.link = link
        self.current_node = current_node
        if self.link.node_1 == self.current_node:
            self.next_node = self.link.node_2
        elif self.link.node_2 == self.current_node:
            self.next_node = self.link.node_1
        else:
            raise ValueError("Node not in link")

    def handle(self):
        self.link.available_space += self.packet.size
        self.link.buffer_occupancy_history.append((self.timestamp, self.link.available_space))
        self.link.link_rate_history.append((self.timestamp, self.packet.size))

        rcpe = ReceivePacketEvent(self.timestamp + float(self.packet.size) / self.link.capacity + self.link.delay, self.packet, self.next_node)


        self.link.network.event_queue.push(rcpe)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "Packet", self.packet.packet_id, "(", self.packet.source.node_id, "->", self.packet.destination.node_id, ")", "leaving buffer at node", self.current_node.node_id, "(link", self.link.link_id, ")"

class PacketAcknowledgementEvent(Event):
    """docstring for PacketAcknowledgementEvent."""
    def __init__(self, timestamp, packet, flow):
        super(PacketAcknowledgementEvent, self).__init__(timestamp)

        self.packet = packet
        self.flow = flow

    def handle(self):
        send_time = self.flow.unacknowledged_packets[self.packet.packet_id]
        round_trip_time = self.timestamp - send_time
        self.flow.round_trip_time_history.append((send_time, round_trip_time)) #TODO should this key be receive time
        del self.flow.unacknowledged_packets[self.packet.packet_id]
        # TODO send more packets?

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "flow", self.flow.flow_id, "acknowledgement of packet", self.packet.packet_id



class Host(object):
    """docstring for Host."""
    def __init__(self, node_id):
        super(Host, self).__init__()
        self.node_id = node_id
        self.routing_table = {}


class Router(object):
    """docstring for Router."""
    def __init__(self, node_id):
        super(Router, self).__init__()
        self.node_id = node_id
        self.routing_table = {}


class Link(object):
    """docstring for Link."""
    def __init__(self, link_id, node_1, node_2, buffer_size, capacity, delay):
        super(Link, self).__init__()
        self.link_id = link_id
        self.node_1 = node_1
        self.node_2 = node_2

        # Array of all times we lost a packet
        self.packets_lost_history = []
        # Array of timestamps, size tuples corresponding to the available space in the buffer at that timestamp
        self.buffer_occupancy_history = []
        # Dict from times to amount of information sent at that time
        self.link_rate_history = []

        self.next_send_time = None
        self.buffer_size = buffer_size

        self.capacity = capacity
        self.available_space = capacity


        self.delay = delay


class Packet(object):
    """docstring for Packet."""
    def __init__(self, packet_id, source, destination):
        super(Packet, self).__init__()
        self.source = source
        self.destination = destination
        self.packet_id = packet_id


class DataPacket(Packet):
    """docstring for DataPacket."""
    def __init__(self, packet_id, source, destination):
        super(DataPacket, self).__init__(packet_id, source, destination)
        self.size = DATA_PACKET_SIZE # All data packets have 1024 bytes


class AcknowledgementPacket(Packet):
    """docstring for AcknowledgementPacket."""
    def __init__(self, packet_id, source, destination):
        super(AcknowledgementPacket, self).__init__(packet_id, source, destination)
        self.size = ACK_PACKET_SIZE # All acknowledgement packets have 64 bytes.





class Flow(object):
    """docstring for Flow."""
    def __init__(self, flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm):
        super(Flow, self).__init__()
        self.flow_id = flow_id
        self.source_host = source_host
        self.destination_host = destination_host

        # Map from received packet ids to their round trip times
        self.round_trip_time_history = []

        self.payload_size = payload_size
        self.start_time = start_time
        self.unacknowledged_packets = {} # map from packet_ids to the times at which they were sent

        self.flow_rate_history = []

    def congestion_control_algorithm(self):
        return WINDOW_SIZE # TODO Jagriti and Nikita will reimplement this

    def setup(self):

        num_packets = self.payload_size / DATA_PACKET_SIZE # TODO

        for packet_id in range(num_packets):

            packet = DataPacket(packet_id, self.source_host, self.destination_host)
            send_time = self.start_time + packet_id * 0.001
            self.unacknowledged_packets[packet_id] = send_time
            self.flow_rate_history.append((send_time, DATA_PACKET_SIZE))
            self.network.event_queue.push(ReceivePacketEvent(send_time, packet, self.source_host))
            # TODO change the one packet per second protocol
