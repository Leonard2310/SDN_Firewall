from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.lib import hub
import time
import statistics
import json

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.port_stats = {}
        self.port_throughput = {}
    
        # Load link bandwidth from file
        self.link_bandwidth = self._load_link_bandwidth('/home/so/Scrivania/Progetto_NCI/link_bandwidth.json')
        
        # Initialize dynamic threshold based on bandwidth
        self.initial_threshold = self.calculate_initial_threshold()
        
        self.throughput_history = {}
        self.monitor_thread = hub.spawn(self._monitor)

    def _load_link_bandwidth(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error('Could not load link bandwidth file: %s', e)
            return {}

    def calculate_initial_threshold(self):
        # Calculate initial threshold based on the bandwidth of the first link in topology
        try:
            first_link_bandwidth = next(iter(self.link_bandwidth.values()))  # Get the bandwidth of the first link
            first_link_bandwidth_value = next(iter(first_link_bandwidth.values()))  # Get the bandwidth value
            initial_threshold = ((first_link_bandwidth_value / 8) * 10**6) * 0.8  # Use 80% of the bandwidth as initial threshold
            return initial_threshold
        except Exception as e:
            self.logger.error('Error calculating initial threshold: %s', e)
            return 750000  # Default value if calculation fails (0.75Mbps)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        self.datapaths[datapath.id] = datapath

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)
    
    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        # Extract the body of the message containing port statistics
        body = ev.msg.body
        
        # Get the datapath ID from the event message
        dpid = ev.msg.datapath.id
        
        # Initialize dictionaries for storing port statistics, throughput, and history if not already initialized
        self.port_stats.setdefault(dpid, {})
        self.port_throughput.setdefault(dpid, {})
        self.throughput_history.setdefault(dpid, {})
        
        # Get the current timestamp for calculating throughput intervals
        timestamp = time.time()

        # Iterate through each port's statistics in the message body
        for stat in body:
            # Extract port number, received bytes, and transmitted bytes from the statistics
            port_no = stat.port_no
            rx_bytes = stat.rx_bytes
            tx_bytes = stat.tx_bytes

            # If port statistics for this datapath and port number are not yet recorded, initialize them
            if port_no not in self.port_stats[dpid]:
                self.port_stats[dpid][port_no] = {'rx_bytes': rx_bytes, 'tx_bytes': tx_bytes, 'timestamp': timestamp}
                continue

            # Calculate the time interval since the last recorded statistics
            prev_stats = self.port_stats[dpid][port_no]
            interval = timestamp - prev_stats['timestamp']

            # Calculate throughput rates in bytes per second for both receive and transmit directions
            rx_throughput = (rx_bytes - prev_stats['rx_bytes']) / interval
            tx_throughput = (tx_bytes - prev_stats['tx_bytes']) / interval

            # Record the calculated throughput rates in the throughput dictionary
            self.port_throughput[dpid][port_no] = {'rx_throughput': rx_throughput, 'tx_throughput': tx_throughput}

            # Add current throughput (sum of RX and TX) to the throughput history for the port
            self.throughput_history[dpid].setdefault(port_no, []).append(rx_throughput + tx_throughput)
            
            # Limit the size of the throughput history to 100 entries to prevent excessive memory usage
            if len(self.throughput_history[dpid][port_no]) > 100:
                self.throughput_history[dpid][port_no].pop(0)

            # Update the port statistics with the current values and timestamp
            self.port_stats[dpid][port_no] = {'rx_bytes': rx_bytes, 'tx_bytes': tx_bytes, 'timestamp': timestamp}

            # Determine the dynamic threshold based on historical throughput data
            if len(self.throughput_history[dpid][port_no]) >= 5:
                mean_throughput = statistics.mean(self.throughput_history[dpid][port_no])
                stddev_throughput = statistics.stdev(self.throughput_history[dpid][port_no])
                dynamic_threshold = mean_throughput + 2 * stddev_throughput
            else:
                # Use initial threshold if there's insufficient historical data
                dynamic_threshold = self.link_bandwidth.get(str(dpid), {}).get(str(port_no), self.initial_threshold)

            # Log the current throughput and dynamic threshold for the port
            self.logger.info('Port %s on switch %s - RX: %s bytes/s, TX: %s bytes/s, Threshold: %s bytes/s', port_no, dpid, rx_throughput, tx_throughput, dynamic_threshold)

            # If current throughput exceeds the dynamic threshold, log a warning and block the port
            if rx_throughput > dynamic_threshold or tx_throughput > dynamic_threshold:
                self.logger.warning('Threshold exceeded on port %s of switch %s', port_no, dpid)
                self._block_port(dpid, port_no)

    def _block_port(self, dpid, port_no):
        # Retrieve the datapath associated with the given datapath ID
        datapath = self.datapaths.get(dpid)
        
        # Check if datapath is found; if not, log an error and return
        if datapath is None:
            self.logger.error('Datapath %s not found', dpid)
            return
        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Create a match to block packets coming from the specified port
        match = parser.OFPMatch(in_port=port_no)
        
        actions = []
        
        # Add a flow entry to drop packets coming from the specified port
        self.add_flow(datapath, 100, match, actions)
        
        self.logger.info('\n---\n---\nBlocking port %s on switch %s\n---\n---\n', port_no, dpid)


# Main function
if __name__ == '__main__':
    from ryu.cmd import manager
    manager.main()
