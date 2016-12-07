
# This file contains all the classes and methods for the basic network architecture

from events import *

DATA_PACKET_SIZE = 1024 * 8
ACK_PACKET_SIZE = 64 * 8
TIMEOUT = 20
#WINDOW_SIZE = 20
BIG = 10**20

class Network(object):
    """Network object for the simulation. This object contains dicts which keep track of all the nodes, links and flows in the network. It also has an event queue and an event loop method to execute the simulation."""

    def __init__(self):
        super(Network, self).__init__()

        # Dicts of all the objects in the network, indexed by their id string
        self.node_dict = dict()
        self.link_dict = dict()
        self.flow_dict = dict()

        self.active_flows = 1

        self.event_queue = EventQueue()


    def add_node(self, node):
        """ Method to add a node to a network. """
        self.node_dict[node.node_id] = node
        node.network = self

    def add_link(self, link_id, node_1, node_2, buffer_size, capacity, delay):
        """ Method to add a link between two nodes in the network. """
        assert node_1.node_id in self.node_dict and self.node_dict[node_1.node_id] == node_1
        assert node_2.node_id in self.node_dict and self.node_dict[node_2.node_id] == node_2
        self.link_dict[link_id] = Link(link_id, node_1, node_2, buffer_size, capacity, delay)
        self.link_dict[link_id].network = self

    def add_flow(self, flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm):
        """ Method to add a flow between two nodes in the network. """
        assert source_host.node_id in self.node_dict and self.node_dict[source_host.node_id] == source_host
        assert destination_host.node_id in self.node_dict and self.node_dict[destination_host.node_id] == destination_host

        self.flow_dict[flow_id] = Flow(flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm)
        source_host.flow = self.flow_dict[flow_id]
        self.flow_dict[flow_id].network = self

        self.flow_dict[flow_id].setup()

    def event_loop(self):
        """ This method starts the event loop, which executes the simulation and runs until the network is no longer sending packets. """

        # Before we start, set up the routing tables of the nodes by telling them every link in the network has cost 1.
        for node_id in self.node_dict:
            node = self.node_dict[node_id]
            node.known_link_costs = {link_id : 1 for link_id in self.link_dict}
            node.update_routing_table()

        # Schedule a routing update for 5 seconds into the simulation
        self.event_queue.push(SendRoutingPacketsEvent(5, self))
        self.active_flows = len(self.flow_dict)

        # Run the event loop until the simulation ends.
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            # ensure correct simulation of delay
            event.print_event_description()
            event.handle()



class Node(object):
    """A Node Object, which is used as a superclass for Hosts and Routers."""
    def __init__(self, node_id):
        super(Node, self).__init__()
        self.node_id = node_id
        self.routing_table = {}
        self.adjacent_links = []

        # For updating the routing table. These represent what the node knows
        # about the other links during an update.
        self.known_link_costs = {}
        self.routing_table_up_to_date = False

    def update_routing_table(self):
        """ This method uses the dict of known link costs (for the whole
        network) to construct a new routing table with Dijkstra's algorithm.
        """

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

                distance_through_node = distance_dict[current_vertex] + self.known_link_costs[link.link_id]

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
        """ Method to get the link corresponding to an adjacent node to this node. """
        for link in self.adjacent_links:
            if link.get_other_node(self).node_id == adjacent_node_id:
                return link

        raise ValueError

    def send_routing_packet(self, destination_node, time_sent):
        """ This method causes a Node to send a routing table packet to a
        certain destination. The routing table packet contains the current
        costs of adjacent links. """

        data_dict = {link.link_id : link.current_cost() for link in self.adjacent_links}

        routing_packet = RoutingPacket("r" + self.node_id + "_" + destination_node.node_id, self, destination_node, time_sent, data_dict)
        self.network.event_queue.push(ReceivePacketEvent(time_sent, routing_packet, self))


class Host(Node):
    """ Host class, subclass of Node."""
    def __init__(self, node_id):
        super(Host, self).__init__(node_id)

        # For a given flow, this gives the id of the next expected packet.
        self.next_expected = {}
        self.rec_pkts = dict()


class Router(Node):
    """Router class, subclass of Node."""
    def __init__(self, node_id):
        super(Router, self).__init__(node_id)




class Link(object):
    """Link object for attaching adjcent nodes."""
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

        # The next time that this Link will be available to send a packet.
        self.next_send_time = None

        # The total size of the buffer in bits.
        self.buffer_size = buffer_size
        # The bandwith capacity, in bits per second, of this link.
        self.capacity = capacity
        # The current amount of available space of the buffer in bits.
        self.available_space = buffer_size
        # The transmission delay of this link.
        self.delay = delay

    def get_other_node(self, node):
        """ A method to get the other node of this link, given one. """
        if self.node_1 == node:
            return self.node_2
        elif self.node_2 == node:
            return self.node_1
        else:
            raise ValueError("Node not in link")

    def current_cost(self):
        """ A method which computes the cost of traversing this link, computed
        from the amount of data in the buffer and the capacity of the link.
        Used for the cost in the shortest path routing algorithm. """
        return float(self.buffer_size - self.available_space)/self.capacity


class Packet(object):
    """ Packet object. """
    def __init__(self, packet_id, source, destination):
        super(Packet, self).__init__()
        self.source = source
        self.destination = destination
        self.packet_id = packet_id


class DataPacket(Packet):
    """ Subclass of Packet for packets which represent host-to-host payload
    comunication."""
    def __init__(self, packet_id, source, destination):
        super(DataPacket, self).__init__(packet_id, source, destination)
        self.size = DATA_PACKET_SIZE # All data packets have 1024 bytes


class AcknowledgementPacket(Packet):
    """ Subclass of Packet for acknowledgement packets."""
    def __init__(self, packet_id, source, destination, ACK):
        super(AcknowledgementPacket, self).__init__(packet_id, source, destination)
        self.size = ACK_PACKET_SIZE # All acknowledgement packets have 64 bytes.
        self.ACK = ACK

class RoutingPacket(Packet):
    """ Subclass of packet for inter-router communication of link costs for
    routing table updates."""
    def __init__(self, packet_id, source, destination, time_sent, data_dict):
        super(RoutingPacket, self).__init__(packet_id, source, destination)
        self.size = DATA_PACKET_SIZE
        self.time_sent = time_sent
        self.data_dict = data_dict


class Flow(object):
    """ Class to represent data flows."""
    def __init__(self, flow_id, source_host, destination_host, payload_size, start_time, congestion_control_algorithm):
        super(Flow, self).__init__()
        self.flow_id = flow_id
        self.source_host = source_host
        self.destination_host = destination_host

        # Map from received packet ids to their round trip times
        self.round_trip_time_history = {}

        self.payload_size = payload_size
        self.start_time = start_time
        # Packets that are in transit, never delete from this, used to calculate round trip time
        # Map from psuhed packet ids to time they were pushed
        self.pushed_packets = {} 
        # packets in transit, map from packet_ids to the times at which they were sent, used in 
        # congestion control
        self.unacknowledged_packets = {} 
        # Packets that need to be sent to source host
        self.unpushed = []
        # an array of timestamp, bytes_sent tuples, used to plot
        self.flow_rate_history = [] 
        # initialize window size to 20
        self.WINDOW_SIZE = 20
        # initialize threshold to 50, used in TCP Reno
        self.THRESHOLD = 500
        # array hold ids of last 3 acknowledgments
        self.prev_ack = [-1, -1, -1]
        # initialize minimum round trip time to a large value
        self.baseRTT = 1000
        # array contains changing values of window size, used to plot
        self.window_size_history = []
        # type of congestion control algorithm
        self.alg_type = congestion_control_algorithm
        # number of packets to be sent and received
        self.num_packets = self.payload_size / DATA_PACKET_SIZE
        # initialize gamma and alpha for TCP Fast
        self.gamma = 0.5
        self.alpha = 15

    # This method updates the window size accordingly if a successful ack occurrs in 
    # the slow start phase.
    def slow_start(self):
        self.WINDOW_SIZE += 1
        return self.WINDOW_SIZE

    # Tis method updates the window size accordingly if a successful ack occurrs in 
    # the congestion avoidance phase
    def cong_avoid(self):
        self.WINDOW_SIZE += 1 / self.WINDOW_SIZE
        return self.WINDOW_SIZE

    # this method implements the TCP Reno congestion control algorithm
    def reno(self, packet, current_time):

        # delete any packet with pcket id less than current one from 
        # unacknowledged packets dictionary since we assume 
        # all packets with id less than current have also been
        # acknowledged
        temp_unack = self.unacknowledged_packets.keys()
        for p in temp_unack:
            if int(p[3:]) < int(packet.ACK[3:]):
                del self.unacknowledged_packets[p]

        # shift last two elements to be first two
        for i in range(2):
            self.prev_ack[i] = self.prev_ack[i + 1]
        # replace last element with new ack
        self.prev_ack[2] = packet.ACK

        # if triple ack occurs
        if self.prev_ack[0] == self.prev_ack[1] and self.prev_ack[1] == self.prev_ack[2]:
            # cut threshold to half of current window size
            self.THRESHOLD = self.WINDOW_SIZE / 2
            # halve window size
            self.WINDOW_SIZE = max(self.WINDOW_SIZE / 2.0, 1.0)
            self.window_size_history.append((current_time, self.WINDOW_SIZE))
            current_time += .01
            # resend lost packet
            if int(packet.ACK[3:]) < self.num_packets and int(packet.ACK[3:]) not in self.unpushed:
                heapq.heappush(self.unpushed, int(packet.ACK[3:]))

        # if successful ack occurrs, update window size accordingly
        else:
            if self.WINDOW_SIZE <= self.THRESHOLD:
                self.window_size_history.append((current_time, self.slow_start()))
            else:
                self.window_size_history.append((current_time, self.cong_avoid()))
            #self.WINDOW_SIZE = self.WINDOW_SIZE + 1.0 / self.WINDOW_SIZE

        self.send(current_time)

    # this method implements the TCP Reno congestion control algorithm
    def fast(self, packet, current_time):
        # delete any packet with pcket id less than current one from 
        # unacknowledged packets dictionary since we assume 
        # all packets with id less than current have also been
        # acknowledged
        temp_unack = self.unacknowledged_packets.keys()
        for p in temp_unack:
            if int(p[3:]) < int(packet.ACK[3:]):
                del self.unacknowledged_packets[p]

        # shift last two elements to be first two
        for i in range(2):
            self.prev_ack[i] = self.prev_ack[i + 1]
        # replace last element with new ack
        self.prev_ack[2] = packet.ACK

        # if duplicate ack occurs
        if self.prev_ack[1] == self.prev_ack[2]:
            # halve window size
            self.WINDOW_SIZE = max(self.WINDOW_SIZE / 2.0, 1.0)
            self.window_size_history.append((current_time, self.WINDOW_SIZE))
            current_time += .01
            # resend lost packet
            if int(packet.ACK[3:]) < self.num_packets and int(packet.ACK[3:]) not in self.unpushed:
                heapq.heappush(self.unpushed, int(packet.ACK[3:]))

        # if a successful ack occurs
        elif int(packet.ACK[3:]) < self.num_packets:
            curr_rtt = self.round_trip_time_history[packet.packet_id]
            # update minimum round trip time
            self.baseRTT = min(self.baseRTT, curr_rtt)
            w = self.WINDOW_SIZE
            # update window size accordingly
            self.WINDOW_SIZE = min(2 * w, (1 - self.gamma) * w + self.gamma * ((self.baseRTT / curr_rtt) * w + self.alpha))
            self.window_size_history.append((current_time, self.WINDOW_SIZE))

        self.send(current_time, False)

    # This method sends packets 
    def send(self, execution_time, timeout = True):
        self.unpushed.sort(reverse = True)
        # while there the number of packets in transit does not reach the window size and 
        # there are packets to send
        while (len(self.unacknowledged_packets) < self.WINDOW_SIZE) and self.unpushed:
            execution_time += .00000001
            packet_num = self.unpushed.pop()
            packet_id = str(self.flow_id) + "_" + str(packet_num)
            self.unacknowledged_packets[packet_id] = execution_time
            self.pushed_packets[packet_id] = execution_time
            packet = DataPacket(packet_id, self.source_host, self.destination_host)
            self.flow_rate_history.append((execution_time, DATA_PACKET_SIZE))
            # send packets and timeout event (if tcp reno)
            self.network.event_queue.push(ReceivePacketEvent(execution_time, packet, self.source_host))

            if timeout:
                self.network.event_queue.push(TimeoutEvent(execution_time + TIMEOUT, packet, self))


    def setup(self):
        global TIMEOUT

        for packet in range(self.num_packets):
            packet_id = packet

            heapq.heappush(self.unpushed, packet_id)

        self.send(self.start_time)
