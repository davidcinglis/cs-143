

from network import *


if __name__ == "__main__":

    n = Network()

    n.add_host("h1")
    n.add_host("h2")

    n.add_link("l1", n.node_dict["h1"], n.node_dict["h2"], 64 * 1000 * 8, 10 * 10**6, 0.01)

    n.add_flow("f1", n.node_dict["h1"], n.node_dict["h2"], 160 * 10**6, 1, None)
