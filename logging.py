from network import *
import numpy
import matplotlib.pyplot as plt
import math

# TODO: Decide where to put the logging functionality
# I decided to put it in a separate file for now for better readability
# but it might make more sense to associate it with the network class

def plot_buffer_occupancy(link):
  """
  This function plots available space in a buffer as a function of time.
  """
  timestamps = [tup[0] for tup in link.buffer_occupancy_history]
  space_values = [tup[1] for tup in link.buffer_occupancy_history]
  plt.plot(timestamps, space_values)
  plt.xlabel('time (seconds)')
  plt.ylabel('available space (bits)')
  plt.show()

def plot_packet_loss(link):
  """
  This function plots packet loss as a function of time for an input link.
  Each data point is the time at which a packet loss occurred.
  """
  # determine the scale of the graph
  timestamps = [tup[0] for tup in link.link_rate_history]
  max_time = math.ceil(max(timestamps))

  timestamps = link.packets_lost_history
  packet_loss_values = [tup[0] + 1 for tup in enumerate(link.packets_lost_history)]

  timestamps.append(max_time)
  packet_loss_values.append(len(packet_loss_values) + 1)
  plt.plot(timestamps, packet_loss_values)
  plt.xlabel('time (seconds)')
  plt.ylabel('packets lost')
  plt.show()

def plot_link_rate(link):
  """
  This functions plots the link rate of the input link.
  It calculates link rate by dividing the timeframe into quarter-second
  intervals and plotting the amount of data that was sent in each interval.
  """
  # determine the scale of the graph
  timestamps = [tup[0] for tup in link.link_rate_history]
  max_time = math.ceil(max(timestamps))

  # creates quarter-second intervals
  intervals = numpy.linspace(0, max_time, max_time * 4)

  # place each transmission into the appropriate interval
  flow_rate_values = []
  idx = 0
  for i in range(len(intervals)):
    bytes_sent = 0
    while idx < len(link.link_rate_history) and link.link_rate_history[idx][0] <= intervals[i]:
      bytes_sent += link.link_rate_history[idx][1]
      idx += 1

    flow_rate_values.append(bytes_sent / 0.5)

  # plot the intervals
  plt.plot(intervals, flow_rate_values)
  plt.xlabel('time (seconds)')
  plt.ylabel('link rate (bits/sec)')
  plt.show()

def plot_flow_rate(flow):
  """
  This functions plots the flow rate of the input flow.
  It calculates link rate by dividing the timeframe into quarter-second
  intervals and plotting the amount of data that was sent in each interval.
  """
  timestamps = [tup[0] for tup in flow.flow_rate_history]
  max_time = math.ceil(max(timestamps))

  # creates quarter-second intervals
  intervals = numpy.linspace(0, max_time, max_time * 4)

  # place each transmission into the appropriate interval
  flow_rate_values = []
  idx = 0
  for i in range(len(intervals)):
    bytes_sent = 0
    while idx < len(flow.flow_rate_history) and flow.flow_rate_history[idx][0] <= intervals[i]:
      bytes_sent += flow.flow_rate_history[idx][1]
      idx += 1

    flow_rate_values.append(bytes_sent / 0.5)

  # plot the intervals
  plt.plot(intervals, flow_rate_values)
  plt.xlabel('time (seconds)')
  plt.ylabel('flow rate (bits/sec)')
  plt.show()