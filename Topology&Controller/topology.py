# Import necessary functions from Mininet
import json
from mininet.log import setLogLevel, info
from mininet.net import Mininet, CLI
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink

# Definition of the Environment class to manage the network simulation
class Environment(object):
    def __init__(self):
        # Initialization of a Mininet network with a remote controller and link specifications
        self.net = Mininet(controller=RemoteController, link=TCLink)
        info("*** Starting controller\n")
        # Adding and starting the controller
        c1 = self.net.addController('c1', controller=RemoteController)  # Controller
        c1.start()
        info("*** Adding hosts and switches\n")
        # Adding hosts (h1 and h2) and switches (cpe1, cpe2, core1) to the network
        self.h1 = self.net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1')
        self.h2 = self.net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2')
        self.h3 = self.net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3')
        self.cpe1 = self.net.addSwitch('s1', cls=OVSKernelSwitch)
        self.cpe2 = self.net.addSwitch('s2', cls=OVSKernelSwitch)
        self.core1 = self.net.addSwitch('s3', cls=OVSKernelSwitch)
        self.cpe3 = self.net.addSwitch('s4', cls=OVSKernelSwitch)
        info("*** Adding links\n")
        # Adding links between hosts and switches with bandwidth and delay specifications
        self.net.addLink(self.h1, self.cpe1, bw=6, delay='0.0025ms')
        self.path1 = self.net.addLink(self.cpe1, self.core1, bw=3, delay='25ms')
        self.net.addLink(self.h2, self.cpe2, bw=6, delay='0.0025ms')
        self.path2 = self.net.addLink(self.cpe2, self.core1, bw=3, delay='25ms')
        self.path3 = self.net.addLink(self.core1, self.cpe3, bw=3, delay='25ms')
        self.net.addLink(self.cpe3, self.h3, bw=6, delay='0.0025ms')
        
        info("*** Starting network\n")
        # Building and starting the Mininet network
        self.net.build()
        self.net.start()
    
        self.export_link_bandwidth()

    def export_link_bandwidth(self):
        link_bandwidth = {}
        for link in self.net.links:
            node1, node2 = link.intf1.node, link.intf2.node
            bw = link.intf1.params.get('bw', None)
            if bw:
                if node1.name not in link_bandwidth:
                    link_bandwidth[node1.name] = {}
                if node2.name not in link_bandwidth:
                    link_bandwidth[node2.name] = {}
                link_bandwidth[node1.name][node2.name] = bw
                link_bandwidth[node2.name][node1.name] = bw

        with open('/home/so/Scrivania/Progetto_NCI/link_bandwidth.json', 'w') as f:
            json.dump(link_bandwidth, f)

# Main function
if __name__ == '__main__':
    # Set log level to 'info'
    setLogLevel('info')
    info('starting the environment\n')
    # Create an instance of the network simulation environment
    env = Environment()
    info("*** Running CLI\n")
    # Start the Mininet command line interface to interact with the simulated network
    CLI(env.net)