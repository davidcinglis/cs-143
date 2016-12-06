
import heapq
import network



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


class SendRoutingPacketsEvent(Event):
    """docstring for SendRoutingPacketsEvent."""
    def __init__(self, timestamp, network):
        super(SendRoutingPacketsEvent, self).__init__(timestamp)
        self.network = network

    def handle(self):

        # Schedule the next routing tables update, but only if there are other events on the queue, or this is the first one
        if not self.network.event_queue.is_empty():
            self.network.event_queue.push(SendRoutingPacketsEvent(self.timestamp + 5, self.network))

            for link_id in self.network.link_dict:
                link = self.network.link_dict[link_id]

            # Update all the routing tables
            for node_id_1 in self.network.node_dict:
                node_1 = self.network.node_dict[node_id_1]

                node_1.known_link_costs = {}
                node_1.routing_table_up_to_date = False

                for node_id_2 in self.network.node_dict:
                    node_2 = self.network.node_dict[node_id_2]

                    node_1.send_routing_packet(node_2, self.timestamp)



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
            if isinstance(self.packet, network.DataPacket):

                # retrieve flow id
                f_id = self.packet.packet_id[0:2]
                # retrieve packet id
                newly_received_id = int(self.packet.packet_id[3:])
                # if we've never received anything from this flow
                if (f_id not in self.receiving_node.rec_pkts):
                    # then expect to receive the first packet
                    #print "Received packets:", self.receiving_node.rec_pkts[f_id]
                    self.receiving_node.rec_pkts[f_id] = set()
                    self.receiving_node.next_expected[f_id] = 0

                # if we haven't already received this packet, add it to the list of rceived packets
                # for this flow
                if newly_received_id not in self.receiving_node.rec_pkts[f_id]:
                    self.receiving_node.rec_pkts[f_id].add(newly_received_id)

                while self.receiving_node.next_expected[f_id] in self.receiving_node.rec_pkts[f_id]:
                    self.receiving_node.next_expected[f_id] += 1

                updated_next_expected_id = None
                updated_next_expected_id = f_id + "_" + str(self.receiving_node.next_expected[f_id])

                # create an ack packet
                ack = network.AcknowledgementPacket(f_id + "_" + str(newly_received_id), self.packet.destination, self.packet.source, updated_next_expected_id)
                # push an event to receive the ack
                self.receiving_node.network.event_queue.push(ReceivePacketEvent(self.timestamp, ack, self.receiving_node))

                #print "Received packets:", self.receiving_node.rec_pkts[f_id]
                #print "Expected packet:", self.receiving_node.next_expected[f_id]


            # if packet is an ack
            elif isinstance(self.packet, network.AcknowledgementPacket):

                    flow = self.receiving_node.flow
                    e = PacketAcknowledgementEvent(self.timestamp, self.packet, flow)
                    self.receiving_node.network.event_queue.push(e)

            elif isinstance(self.packet, network.RoutingPacket):

                for link_id in self.packet.data_dict:
                    self.receiving_node.known_link_costs[link_id] = self.packet.data_dict[link_id]

                if len(self.receiving_node.network.link_dict) == len(self.receiving_node.known_link_costs) and not self.receiving_node.routing_table_up_to_date:

                    self.receiving_node.update_routing_table()
                    self.routing_table_up_to_date = True



        else:
            next_link = self.receiving_node.routing_table[self.packet.destination.node_id]
            assert isinstance(next_link, network.Link)
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
            self.flow.round_trip_time_history[self.packet.packet_id] = round_trip_time
            if round_trip_time < self.flow.baseRTT:
                self.flow.baseRTT = round_trip_time

        if self.flow.alg_type == "reno":
            self.flow.reno(self.packet, self.timestamp)
        else:
            self.flow.fast(self.packet, self.timestamp)

    def print_event_description(self):
        print "Timestamp:", self.timestamp, "flow", self.flow.flow_id, "acknowledgement of packet", self.packet.packet_id

class TimeoutEvent(Event):
    def __init__(self, timestamp, packet, flow):
        super(TimeoutEvent, self).__init__(timestamp)
        self.packet = packet
        self.flow = flow

    def handle(self):
        packet_num = int(self.packet.packet_id[3:])

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
