
import heapq



# This file contains all the classes and methods for the basic network architecture


DATA_PACKET_SIZE = 1024 * 8
ACK_PACKET_SIZE = 64 * 8
TIME = 0
TIMEOUT = 0.2
#WINDOW_SIZE = 20

class Network(object):
    """docstring for Network."""

    def __init__(self):
        super(Network, self).__init__()
        self.node_dict = dict()
        self.link_dict = dict()
        self.flow_dict = dict()
        self.ack_dict = dict()

        self.active_flows = 0

        self.event_queue = []




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
        # while event queue is not empty, pop and handle event
        while self.event_queue:
            self.event_queue = sorted(self.event_queue, key=lambda x: x.timestamp, reverse=True)
            event = self.event_queue.pop()
            global TIME
            # ensure correct simulation of delay
            if event.timestamp > TIME:
                TIME = event.timestamp
            event.handle()
            event.print_event_description()





class Event(object):
    """docstring for Event."""
    def __init__(self, timestamp):
        super(Event, self).__init__()
        self.timestamp = timestamp

    def __cmp__(self, other):
        return self.timestamp - other.timestamp



class ReceivePacketEvent(Event):
    """docstring for ReceivePacketEvent."""
    def __init__(self, timestamp, packet, receiving_node):
        super(ReceivePacketEvent, self).__init__(timestamp)

        self.packet = packet
        self.receiving_node = receiving_node

    def handle(self):

        # if we are at the destination
        if self.packet.destination == self.receiving_node:
            # if the packet is a data packet, create an acknowledgement and push an event to receive the acknowledgement
            if isinstance(self.packet, DataPacket):
                print "CREATING ACK", "\n\n\n\n"
                print self.packet.packet_id
                # retrieve flow id
                f_id = self.packet.packet_id[0:2]
                # retrieve packet id
                p_id = self.packet.packet_id[3:]
                # if we've never received anything from this flow
                if (f_id not in self.receiving_node.next_exp):
                    # then expect to receive the first packet
                    self.receiving_node.next_exp[f_id] = 0
                # get id of packet that we're expecting next
                new_id = f_id + "_" + str(self.receiving_node.next_exp[f_id])
                # create an ack packet
                ack = AcknowledgementPacket(new_id, self.packet.destination, self.packet.source)
                # push an event to receive the ack
                heapq.heappush(self.receiving_node.network.event_queue, ReceivePacketEvent(self.timestamp, ack, self.receiving_node))
                # if the expected packet is the current packet, expect the next packet
                if (self.receiving_node.next_exp[f_id] == int(p_id)):
                    self.receiving_node.next_exp[f_id] += 1

            # if packet is an ack
            elif isinstance(self.packet, AcknowledgementPacket):

                flow = self.receiving_node.flow
                e = PacketAcknowledgementEvent(self.timestamp, self.packet, flow)
                heapq.heappush(self.receiving_node.network.event_queue, e)

        else:
            next_link = self.receiving_node.routing_table[self.packet.destination.node_id]
            assert isinstance(next_link, Link)
            heapq.heappush(self.receiving_node.network.event_queue, EnterBufferEvent(self.timestamp, self.packet, next_link, self.receiving_node))



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

            heapq.heappush(self.link.network.event_queue, lbe)
        else:
            print "PACKET LOST HAAAALP: " + str(self.packet.packet_id)
            print "\n\n"
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

        heapq.heappush(self.link.network.event_queue, rcpe)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "Packet", self.packet.packet_id, "(", self.packet.source.node_id, "->", self.packet.destination.node_id, ")", "leaving buffer at node", self.current_node.node_id, "(link", self.link.link_id, ")"

class PacketAcknowledgementEvent(Event):
    """docstring for PacketAcknowledgementEvent."""
    def __init__(self, timestamp, packet, flow):
        super(PacketAcknowledgementEvent, self).__init__(timestamp)
        self.packet = packet
        self.flow = flow

    def handle(self):
        if self.packet.packet_id in self.flow.unacknowledged_packets:
            send_time = self.flow.unacknowledged_packets[self.packet.packet_id]
            round_trip_time = self.timestamp - send_time
            self.flow.round_trip_time_history[send_time] = round_trip_time #TODO should this key be receive time
            del self.flow.unacknowledged_packets[self.packet.packet_id]
            
        self.flow.congestion_control_algorithm(self.packet.packet_id)
        # TODO send more packets?

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "flow", self.flow.flow_id, "acknowledgement of packet", self.packet.packet_id

class TimeoutEvent(Event):
    def __init__(self, timestamp, packet, flow):
        super(TimeoutEvent, self).__init__(timestamp)
        self.packet = packet
        self.flow = flow

    def handle(self):
        packet_num = self.packet.packet_id[3:]
        if self.packet.packet_id  in self.flow.unacknowledged_packets:
            print "TIMEOUT EVENT OCCURRING"
            
            self.flow.WINDOW_SIZE = max(self.flow.WINDOW_SIZE / 2.0, 1.0)
            print "\n\n", self.flow.WINDOW_SIZE
            heapq.heappush(self.flow.unpushed, packet_num)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "flow", self.flow.flow_id, "checking timeout for packet", self.packet.packet_id

class Host(object):
    """docstring for Host."""
    def __init__(self, node_id):
        super(Host, self).__init__()
        self.node_id = node_id
        self.routing_table = {}

        # For a given flow, this gives the id of the next expected packet.
        self.next_exp = {}


class Router(object):
    """docstring for Router."""
    def __init__(self, node_id):
        super(Router, self).__init__()
        self.node_id = node_id
        #self.routing_table = routing_table


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
        self.round_trip_time_history = {}

        self.payload_size = payload_size
        self.start_time = start_time
        self.unacknowledged_packets = {} # map from packet_ids to the times at which they were sent
        #self.acknowledged_packets = {} # map fromr packet_ids to # of times they have been acknowledged
        self.unpushed = []
        self.flow_rate_history = []
        self.WINDOW_SIZE = 20
        self.prev_ack = [-1, -1, -1]

        self.bytes_sent = 0


    def congestion_control_algorithm(self, packet_id):
        # shift last two elements to be first two
        global TIME 
        for i in range(2):
            self.prev_ack[i] = self.prev_ack[i + 1]
        # replace last element with new ack
        self.prev_ack[2] = packet_id
        print self.prev_ack

        if self.prev_ack[0] == self.prev_ack[1] and self.prev_ack[1] == self.prev_ack[2]:
            print "packet triple ack on id: " + str(self.prev_ack)
            self.WINDOW_SIZE = max(self.WINDOW_SIZE / 2.0, 1.0)
            TIME = TIME + .001
            self.unacknowledged_packets[packet_id] = TIME
            packet = DataPacket(packet_id, self.source_host, self.destination_host)
            heapq.heappush(self.network.event_queue, ReceivePacketEvent(TIME, packet, self.source_host))

        else:
            self.WINDOW_SIZE = self.WINDOW_SIZE + 1.0 / self.WINDOW_SIZE
            self.bytes_sent -= 1024

        print "WINDOW SIZE:", self.WINDOW_SIZE
        while (len(self.unacknowledged_packets) < self.WINDOW_SIZE) and self.unpushed:
            TIME = TIME + .001
            packet_num = self.unpushed.pop()
            packet_id = str(self.flow_id) + "_" + str(packet_num)


            self.bytes_sent += 1024

            self.unacknowledged_packets[packet_id] = TIME
            packet = DataPacket(packet_id, self.source_host, self.destination_host)
            heapq.heappush(self.network.event_queue, ReceivePacketEvent(TIME, packet, self.source_host))



    def setup(self):
        global TIMEOUT

        num_packets = self.payload_size / DATA_PACKET_SIZE # TODO

        for packet in range(num_packets):
            packet_id = packet 
            
            heapq.heappush(self.unpushed, packet_id)

        self.unpushed = sorted(self.unpushed, reverse=True)


        for packet in range(self.WINDOW_SIZE):
            # need to figure out delay
            packet_num= self.unpushed.pop()

            packet_id = str(self.flow_id) + "_" + str(packet_num)
            packet = DataPacket(packet_id, self.source_host, self.destination_host)
            #send_time = self.start_time + packet_id * 0.001
            # find some way of delaying flow
            send_time = self.start_time + int(packet_id[3:]) * .001 
            self.unacknowledged_packets[packet_id] = send_time
            #self.acknowledged_packets[packet_id] = 0
            self.flow_rate_history.append((send_time, DATA_PACKET_SIZE))
            heapq.heappush(self.network.event_queue, ReceivePacketEvent(send_time, packet, self.source_host))
            heapq.heappush(self.network.event_queue, TimeoutEvent(send_time + TIMEOUT, packet, self))
            # TODO change the one packet per second protocol
