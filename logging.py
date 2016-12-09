from network import *
import numpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import math

def plot_buffer_occupancy(links):
  """
  This function plots buffer occupancy as a function of time.
  """

  colors = cm.rainbow(numpy.linspace(0, 1, len(links)))
  for link, color in zip(links, colors):
    timestamps = [tup[0] for tup in link.buffer_occupancy_history]
    space_values = [tup[1] for tup in link.buffer_occupancy_history]
    intervals, bucket_values = bucket_average(timestamps, space_values)
    bucket_values = [link.buffer_size - val for val in bucket_values]
    smoothed_values = sliding_window_average(bucket_values, 10)
    plt.plot(intervals, smoothed_values, color=color, label=link.link_id)
  plt.title('Link Buffer Occupancy')

  plt.xlabel('time (seconds)')
  plt.ylabel('utilized space (bits)')
  plt.legend()
  plt.show()

def plot_packet_loss(links):
  """
  This function plots packet loss as a function of time for an input link.
  Each data point is the time at which a packet loss occurred.
  """

  colors = cm.rainbow(numpy.linspace(0, 1, len(links)))
  for link, color in zip(links, colors):

    # need to calculate the max timestamp from link rate to handle the case with no packet loss
    max_time = max([tup[0] for tup in link.link_rate_history])
    timestamps = link.packets_lost_history
    values = [1 for event in link.packets_lost_history]

    # add a dummy value so we're guaranteed to have something in the arry
    timestamps.append(max_time)
    values.append(0)
    bucket_timestamps, bucket_values = bucket_sum(timestamps, values)
    plt.plot(bucket_timestamps, bucket_values, color=color, label=link.link_id)

  plt.title('Packet Loss')
  plt.xlabel('time (seconds)')
  plt.ylabel('packets lost')
  plt.legend()
  plt.show()

def plot_link_rate(links):
  """
  This functions plots the link rate of the input link.
  It calculates link rate by dividing the timeframe into quarter-second
  intervals and plotting the amount of data that was sent in each interval.
  """

  colors = cm.rainbow(numpy.linspace(0, 1, len(links)))
  for link, color in zip(links, colors):
    timestamps = [tup[0] for tup in link.link_rate_history]
    transmission_events = [tup[1] for tup in link.link_rate_history]
    intervals, link_rate_values = bucket_sum(timestamps, transmission_events)
    plt.plot(intervals, sliding_window_average(link_rate_values, 10), color=color, label=link.link_id)

  plt.title('Link Rate')
  plt.xlabel('time (seconds)')
  plt.ylabel('link rate (bits/sec)')
  plt.legend()
  plt.show()

def plot_flow_rate(flows):
  """
  This functions plots the flow rate of the input flow.
  It calculates link rate by dividing the timeframe into quarter-second
  intervals and plotting the amount of data that was sent in each interval.
  """

  colors = cm.rainbow(numpy.linspace(0, 1, len(flows)))
  for flow, color in zip(flows, colors):
    timestamps = [tup[0] for tup in flow.flow_rate_history]
    transmission_events = [tup[1] for tup in flow.flow_rate_history]
    intervals, flow_rate_values = bucket_sum(timestamps, transmission_events)
    smoothed_values = sliding_window_average(flow_rate_values, 10)
    plt.plot(intervals, smoothed_values, color=color, label=flow.flow_id)

  plt.title('Flow Rate')
  plt.xlabel('time (seconds)')
  plt.ylabel('flow rate (bits/sec)')
  plt.legend()
  plt.show()

def plot_round_trip_time(flows):

  colors = cm.rainbow(numpy.linspace(0, 1, len(flows)))
  for flow, color in zip(flows, colors):

    send_time_tuples = sorted(flow.pushed_packets.items(), key=lambda x:x[1])
    timestamps = [tup[1] for tup in send_time_tuples]
    raw_rtts = [flow.round_trip_time_history[tup[0]] for tup in send_time_tuples
                if tup[0] in flow.round_trip_time_history]
    intervals, rtt_bucket_values = bucket_average(timestamps, raw_rtts)
    smoothed_values = sliding_window_average(rtt_bucket_values, 10)
    plt.plot(intervals, smoothed_values, color=color, label=flow.flow_id)

  plt.title('Average Round Trip Time')
  plt.xlabel('time (seconds)')
  plt.ylabel('avg round trip time (secs)')
  plt.legend()
  plt.show()

def plot_window_size(flows):

  colors = cm.rainbow(numpy.linspace(0, 1, len(flows)))
  for flow, color in zip(flows, colors):
    timestamps = [tup[0] for tup in flow.window_size_history]
    window_sizes = [tup[1] for tup in flow.window_size_history]
    intervals, bucket_values = bucket_average(timestamps, window_sizes)
    plt.plot(intervals, sliding_window_average(bucket_values, 10), color=color, label=flow.flow_id)

  plt.title('Window Size')
  plt.xlabel('time (seconds)')
  plt.ylabel('window size (packets)')
  plt.legend()
  plt.show()

def sliding_window_average(raw, window_size):
  """
  This function performs a sliding window average on a set of raw data points.
  Each input is transformed by averaging it with its n previous neighbors and n subsequent neighbors,
  where n is the input window size parameter.
  If the array element is too close to the beginning or end, the first and last element
  of the array will be given extra weight to account for the missing elements beyond them.
  :param raw: The raw data to transform (array)
  :param window_size: The number of neighbors to average over (int)
  :return: An array of the transformed data.
  """
  out = []

  for idx in range(len(raw)):
    window = range(idx - window_size, idx + window_size + 1)
    window_values = []
    for point in window:
      if point < 0:
        window_values.append(raw[0])
      elif point >= len(raw):
        window_values.append(raw[-1])
      else:
        window_values.append(raw[point])
    out.append(numpy.mean(window_values))
  return out

def bucket_average(raw_timestamps, raw_data):
  """
  This function takes a set of events and corresponding timestamps, and constructs
  a series of buckets at one-second intervals, placing each event into the appropriate bucket.
  The output value for each bucket is the average of all the event values in that bucket.
  :param raw_timestamps: Array of raw timestamps
  :param raw_data: Array of events occurring at the above timestamps
  :return: (1) an array of interval values, and (2) an array of averages corresponding to each interval value
  """
  max_timestamp = math.ceil(max(raw_timestamps))
  intervals = numpy.linspace(0, max_timestamp, max_timestamp)

  bucket_values = []
  idx = 0
  for interval in intervals:
    interval_values = []
    while idx < len(raw_data) and raw_timestamps[idx] <= interval:
      interval_values.append(raw_data[idx])
      idx += 1

    if len(interval_values) > 0:
      bucket_values.append(numpy.mean(interval_values))
    elif len(bucket_values) > 0:
      bucket_values.append(bucket_values[-1])
    else:
      bucket_values.append(0)

  return intervals, bucket_values

def bucket_sum(raw_timestamps, raw_data):
  """
  Identical to the above function, except that each bucket is the sum of its elements instead of the average.
  """
  max_timestamp = math.ceil(max(raw_timestamps))
  intervals = numpy.linspace(0, max_timestamp, max_timestamp)

  bucket_values = []
  idx = 0
  for interval in intervals:
    interval_sum = 0
    while idx < len(raw_data) and raw_timestamps[idx] <= interval:
      interval_sum += raw_data[idx]
      idx += 1

    if interval_sum > 0:
      bucket_values.append(interval_sum)
    else:
      bucket_values.append(0)

  return intervals, bucket_values