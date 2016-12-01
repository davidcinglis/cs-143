
# This file contains all the classes and methods for the basic network architecture
import heapq

DATA_PACKET_SIZE = 1024 * 8
ACK_PACKET_SIZE = 64 * 8
TIMEOUT = 20
#WINDOW_SIZE = 20
BIG = 10**20

class Network(object):
    """docstring for Network."""

    def __init__(self):
        super(Network, self).__init__()
        self.node_dict = dict()
        self.link_dict = dict()
        self.flow_dict = dict()
        self.ack_dict = dict()

        self.active_flows = 1

        self.event_queue = EventQueue()


    def add_node(self, node):
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

        self.event_queue.push(UpdateAllRoutingTablesEvent(-1, self))
        self.active_flows = len(self.flow_dict)

        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            # ensure correct simulation of delay
            event.print_event_description()
            event.handle()


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


class UpdateAllRoutingTablesEvent(Event):
    """docstring for UpdateAllRoutingTablesEvent."""
    def __init__(self, timestamp, network):
        super(UpdateAllRoutingTablesEvent, self).__init__(timestamp)
        self.network = network

    def handle(self):

        for link_id in self.network.link_dict:
            link = self.network.link_dict[link_id]
            print link.link_id, link.buffer_size, link.available_space

        # Update all the routing tables (Pscyhically, for now) TODO fix this
        for node_id in self.network.node_dict:
            node = self.network.node_dict[node_id]
            node.update_routing_table()

        # Schedule the next routing tables update, but only if there are other events on the queue, or this is the first one
        if not self.network.event_queue.is_empty():
            self.network.event_queue.push(UpdateAllRoutingTablesEvent(self.timestamp + 5, self.network))

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "Executed an update of routing tables."



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

                print "CREATING ACK", self.packet.packet_id
                # retrieve flow id
                f_id = self.packet.packet_id[0:2]
                # retrieve packet id
                p_id = int(self.packet.packet_id[3:])
                # if we've never received anything from this flow
                if (f_id not in self.receiving_node.rec_pkts):
                    # then expect to receive the first packet
                    #print "Received packets:", self.receiving_node.rec_pkts[f_id]
                    self.receiving_node.rec_pkts[f_id] = []
                    self.receiving_node.next_expected[f_id] = 0

                # if we haven't already received this packet, add it to the list of rceived packets
                # for this flow
                if p_id not in self.receiving_node.rec_pkts[f_id]:
                    self.receiving_node.rec_pkts[f_id].append(p_id)

                # sort the receiving packets in ascending order
                self.receiving_node.rec_pkts[f_id].sort()

                new_id = -1
                if p_id == self.receiving_node.next_expected[f_id]:
                    new_id = f_id + "_" + str(self.receiving_node.next_expected[f_id])

                for p_id in self.receiving_node.rec_pkts[f_id]:
                    # packet we are on is not the one are expecting, so keep looking
                    if p_id < self.receiving_node.next_expected[f_id]:
                        continue
                    # if we have received the expected packet, increment value of expected packet
                    elif p_id == self.receiving_node.next_expected[f_id]:
                        self.receiving_node.next_expected[f_id] += 1
                    else:
                        break

                # ** check this
                # current packet is the expected one
                if new_id == -1:
                    new_id = f_id + "_" + str(self.receiving_node.next_expected[f_id])

                # create an ack packet
                print "NEW_ID", new_id, p_id
                ack = AcknowledgementPacket(new_id, self.packet.destination, self.packet.source)
                # push an event to receive the ack
                self.receiving_node.network.event_queue.push(ReceivePacketEvent(self.timestamp, ack, self.receiving_node))

                #print "Received packets:", self.receiving_node.rec_pkts[f_id]
                #print "Expected packet:", self.receiving_node.next_expected[f_id]


            # if packet is an ack
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
        self.next_node = self.link.get_other_node(self.current_node)


    def handle(self):
        self.link.available_space += self.packet.size
        self.link.buffer_occupancy_history.append((self.timestamp, self.link.available_space))
        self.link.link_rate_history.append((self.timestamp, self.packet.size))

        rcpe = ReceivePacketEvent(self.timestamp + float(self.packet.size) / self.link.capacity + self.link.delay, self.packet, self.next_node)


        self.link.network.event_queue.push(rcpe)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "Packet", self.packet.packet_id, "(", self.packet.source.node_id, "->", self.packet.destination.node_id, ")", "leaving buffer at node", self.current_node.node_id, "(link", self.link.link_id, ")"
        pass


class PacketAcknowledgementEvent(Event):
    """docstring for PacketAcknowledgementEvent."""
    def __init__(self, timestamp, packet, flow):
        super(PacketAcknowledgementEvent, self).__init__(timestamp)
        self.packet = packet
        self.flow = flow

    def handle(self):
        if self.packet.packet_id in self.flow.pushed_packets:
            send_time = self.flow.pushed_packets[self.packet.packet_id]
            round_trip_time = self.timestamp - send_time
            print "Timestamp\n\n", self.timestamp, send_time
            print self.packet.packet_id
            self.flow.round_trip_time_history[self.packet.packet_id] = round_trip_time
            if round_trip_time < self.flow.baseRTT:
                self.flow.baseRTT = round_trip_time

        if self.flow.alg_type == "reno":
            self.flow.reno(self.packet.packet_id, self.timestamp)
        else:
            self.flow.fast(self.packet.packet_id, self.timestamp)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "flow", self.flow.flow_id, "acknowledgement of packet", self.packet.packet_id

class TimeoutEvent(Event):
    def __init__(self, timestamp, packet, flow):
        super(TimeoutEvent, self).__init__(timestamp)
        self.packet = packet
        self.flow = flow

    def handle(self):
        packet_num = int(self.packet.packet_id[3:])
        print "TIMEOUT EVENT OCCURRING", packet_num

        # if timeout acually happens
        if self.packet.packet_id  in self.flow.unacknowledged_packets:
            print "Timestamp:", self.timestamp, "packet_id", self.packet.packet_id, "TIMEOUT OCCURRED"
            del self.flow.unacknowledged_packets[self.packet.packet_id]
            #self.flow.WINDOW_SIZE = max(self.flow.WINDOW_SIZE / 2.0, 1.0)

            # reset the window size to 1
            self.flow.WINDOW_SIZE = 1
            self.flow.window_size_history.append((self.timestamp, self.flow.WINDOW_SIZE))
            self.THRESHOLD = self.flow.WINDOW_SIZE / 2.0
            heapq.heappush(self.flow.unpushed, packet_num)
            self.flow.send(self.timestamp)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "flow", self.flow.flow_id, "checking timeout for packet", self.packet.packet_id


class Node(object):
    """docstring for Node."""
    def __init__(self, node_id):
        super(Node, self).__init__()
        self.node_id = node_id
        self.routing_table = {}
        self.adjacent_links = []

    def update_routing_table(self):

        unvisited_nodes = {node_id for node_id in self.network.node_dict}
        distance_dict = {node_id : BIG for node_id in self.network.node_dict}
        previous_dict = {node_id : None for node_id in self.network.node_dict}

        distance_dict[self.node_id] = 0

        while unvisited_nodes:

            min_dist = min(distance_dict[node] for node in unvisited_nodes)
            current_vertex = [node for node in unvisited_nodes if distance_dict[node] == min_dist][0]

            unvisited_nodes.remove(current_vertex)

            for link in self.network.node_dict[current_vertex].adjacent_links:
                adj_node = link.get_other_node(self.network.node_dict[current_vertex])

                distance_through_node = distance_dict[current_vertex] + link.current_cost()

                if distance_through_node < distance_dict[adj_node.node_id]:
                    distance_dict[adj_node.node_id] = distance_through_node
                    previous_dict[adj_node.node_id] = current_vertex


        for node_id in self.network.node_dict:
            if node_id == self.node_id:
                continue
            traceback_node_id = node_id
            while previous_dict[traceback_node_id] != self.node_id:
                traceback_node_id = previous_dict[traceback_node_id]



            self.routing_table[node_id] = self.get_link_from_node_id(traceback_node_id)


    def get_link_from_node_id(self, adjacent_node_id):
        for link in self.adjacent_links:
            if link.get_other_node(self).node_id == adjacent_node_id:
                return link

        raise ValueError


class Host(Node):
    """docstring for Host."""
    def __init__(self, node_id):
        super(Host, self).__init__(node_id)

        # For a given flow, this gives the id of the next expected packet.
        self.next_expected = {}
        self.rec_pkts = dict()


class Router(Node):
    """docstring for Router."""
    def __init__(self, node_id):
        super(Router, self).__init__(node_id)




class Link(object):
    """docstring for Link."""
    def __init__(self, link_id, node_1, node_2, buffer_size, capacity, delay):
        super(Link, self).__init__()
        self.link_id = link_id
        self.node_1 = node_1
        self.node_2 = node_2

        self.node_1.adjacent_links.append(self)
        self.node_2.adjacent_links.append(self)

        # Array of all times we lost a packet
        self.packets_lost_history = []
        # Array of timestamps, size tuples corresponding to the available space in the buffer at that timestamp
        self.buffer_occupancy_history = []
        # Dict from times to amount of information sent at that time
        self.link_rate_history = []

        self.next_send_time = None
        self.buffer_size = buffer_size


        self.capacity = capacity
        self.available_space = buffer_size

        self.delay = delay

    def get_other_node(self, node):

        if self.node_1 == node:
            return self.node_2
        elif self.node_2 == node:
            return self.node_1
        else:
            raise ValueError("Node not in link")

    def current_cost(self):
        return float(self.buffer_size - self.available_space)/self.capacity


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
        self.pushed_packets = {} # never delete from this
        self.unacknowledged_packets = {} # map from packet_ids to the times at which they were sent
        #self.acknowledged_packets = {} # map fromr packet_ids to # of times they have been acknowledged
        self.unpushed = []
        self.flow_rate_history = [] # an array of timestamp, bytes_sent tuples
        self.WINDOW_SIZE = 20
        self.THRESHOLD = 64
        self.prev_ack = [-1, -1, -1]
        self.baseRTT = 1000
        self.window_size_history = []
        self.alg_type = congestion_control_algorithm
        self.num_packets = self.payload_size / DATA_PACKET_SIZE


    def slow_start(self):
        self.WINDOW_SIZE += 1
        return self.WINDOW_SIZE

    def cong_avoid(self):
        self.WINDOW_SIZE += 1 / self.WINDOW_SIZE
        return self.WINDOW_SIZE


    def reno(self, packet_id, current_time):

        num_packets = self.payload_size / DATA_PACKET_SIZE
        print "calling congestion control alg"

        temp_unack = self.unacknowledged_packets.keys()
        for p in temp_unack:
            if int(p[3:]) <= int(packet_id[3:]):
                del self.unacknowledged_packets[p]

        # shift last two elements to be first two
        for i in range(2):
            self.prev_ack[i] = self.prev_ack[i + 1]
        # replace last element with new ack
        self.prev_ack[2] = packet_id

        # if triple ack occurs
        if self.prev_ack[0] == self.prev_ack[1] and self.prev_ack[1] == self.prev_ack[2]:
            print "packet triple ack on id: " + str(self.prev_ack)
            # cut threshold to half
            self.THRESHOLD = self.WINDOW_SIZE / 2
            self.WINDOW_SIZE = max(self.WINDOW_SIZE / 2.0, 1.0)
            self.window_size_history.append((current_time, self.WINDOW_SIZE))
            current_time += .01
            if int(packet_id[3:]) < num_packets and int(packet_id[3:]) not in self.unpushed:
                heapq.heappush(self.unpushed, int(packet_id[3:]))

        else:
            if self.WINDOW_SIZE <= self.THRESHOLD:
                self.window_size_history.append((current_time, self.slow_start()))
            else:
                self.window_size_history.append((current_time, self.cong_avoid()))
            #self.WINDOW_SIZE = self.WINDOW_SIZE + 1.0 / self.WINDOW_SIZE

        self.send(current_time)


    def fast(self, packet_id, current_time):

        print "calling congestion control alg"

        temp_unack = self.unacknowledged_packets.keys()
        for p in temp_unack:
            if int(p[3:]) <= int(packet_id[3:]):
                del self.unacknowledged_packets[p]

        # shift last two elements to be first two
        for i in range(2):
            self.prev_ack[i] = self.prev_ack[i + 1]
        # replace last element with new ack
        self.prev_ack[2] = packet_id

        # if triple ack occurs
        if self.prev_ack[1] == self.prev_ack[2]:
            print "packet triple ack on id: " + str(self.prev_ack)
            self.WINDOW_SIZE = max(self.WINDOW_SIZE / 2.0, 1.0)
            self.window_size_history.append((current_time, self.WINDOW_SIZE))
            current_time += .01
            if int(packet_id[3:]) < self.num_packets: #and int(packet_id[3:]) not in self.unpushed:
                print "pushing if double ack"
                heapq.heappush(self.unpushed, int(packet_id[3:]))



        elif int(packet_id[3:]) < self.num_packets:
            curr_rtt = self.round_trip_time_history[packet_id]
            self.baseRTT = min(self.baseRTT, curr_rtt)
            gamma = 0.5
            alpha = 15
            w = self.WINDOW_SIZE
            print "old window size: %f" % self.WINDOW_SIZE
            print "base rtt %f" % self.baseRTT
            print "curr rtt %f" % curr_rtt
            self.WINDOW_SIZE = min(2 * w, (1 - gamma) * w + gamma * ((self.baseRTT / curr_rtt) * w + alpha))
            print "new window size: %f" % self.WINDOW_SIZE
            #self.WINDOW_SIZE = 1
            self.window_size_history.append((current_time, self.WINDOW_SIZE))

        self.send(current_time)

    def send(self, execution_time):
        self.unpushed.sort(reverse = True)

        print len(self.unacknowledged_packets), self.WINDOW_SIZE, len(self.unpushed)

        while (len(self.unacknowledged_packets) < self.WINDOW_SIZE) and self.unpushed:
            execution_time += .01
            packet_num = self.unpushed.pop()
            packet_id = str(self.flow_id) + "_" + str(packet_num)
            self.unacknowledged_packets[packet_id] = execution_time
            self.pushed_packets[packet_id] = execution_time
            packet = DataPacket(packet_id, self.source_host, self.destination_host)
            self.flow_rate_history.append((execution_time, DATA_PACKET_SIZE))
            self.network.event_queue.push(ReceivePacketEvent(execution_time, packet, self.source_host))
            if self.alg_type == "reno":
                self.network.event_queue.push(TimeoutEvent(execution_time + TIMEOUT, packet, self))


    def setup(self):
        global TIMEOUT

        for packet in range(self.num_packets):
            packet_id = packet

            heapq.heappush(self.unpushed, packet_id)

        self.send(self.start_time)
