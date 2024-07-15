import time
import json
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.lib import hub

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.port_stats = {}
        self.port_throughput = {}
        self.security_priority = 100
        
        # Load link bandwidth from file
        self.link_bandwidth = self._load_link_bandwidth('/home/so/Scrivania/Progetto_NCI/link_bandwidth.json')
        
        # Initialize dynamic threshold based on bandwidth
        self.initial_threshold = self.calculate_initial_threshold()
        
        self.throughput_history = {}
        self.max_throughput_history = {}  # Dictionary to store maximum throughput
        self.monitor_thread = hub.spawn(self._monitor)
        
        # Dictionary to track blocked ports and their last exceeded time
        self.blocked_ports = {}

        # Dictionary to track the time throughput has stayed below threshold
        self.below_threshold_time = {}

        # Dictionary to track the time throughput has been above threshold
        self.above_threshold_time = {}

        # Timeout for unlocking a port 
        self.unlock_timeout = 10  # seconds

        # Time that throughput must stay above threshold to trigger block
        self.block_window = 5  # seconds

        # Dictionary to track the last unblock time of ports
        self.last_unblock_time = {}

        # Timestamp for the last log
        self.last_log_time = time.time()

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
            hub.sleep(1)  # Check throughput every second

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
        
        # Initialize dictionaries to store port statistics, throughput, and history if not already initialized
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

            # Update the port statistics with the current values and timestamp
            self.port_stats[dpid][port_no] = {'rx_bytes': rx_bytes, 'tx_bytes': tx_bytes, 'timestamp': timestamp}

            # Check if the current throughput exceeds the dynamic threshold and take appropriate actions
            self.check_port_threshold(dpid, port_no, rx_throughput, tx_throughput, timestamp)

        # Log port statistics every 10 seconds
        if timestamp - self.last_log_time >= 10:
            for dpid in self.port_throughput:
                for port_no in self.port_throughput[dpid]:
                    rx_throughput = self.port_throughput[dpid][port_no]['rx_throughput']
                    tx_throughput = self.port_throughput[dpid][port_no]['tx_throughput']
                    dynamic_threshold = self.link_bandwidth.get(str(dpid), {}).get(str(port_no), self.initial_threshold)
                    self.logger.info('Port %s on switch %s - RX: %s bytes/s, TX: %s bytes/s, Threshold: %s bytes/s',
                                    port_no, dpid, rx_throughput, tx_throughput, dynamic_threshold)
            self.last_log_time = timestamp


    def check_port_threshold(self, dpid, port_no, rx_throughput, tx_throughput, timestamp):
        # Calculate the dynamic threshold based on configured link bandwidth or use default
        dynamic_threshold = self.link_bandwidth.get(str(dpid), {}).get(str(port_no), self.initial_threshold)
        
        # Check if current throughput exceeds the dynamic threshold
        if (rx_throughput > dynamic_threshold or tx_throughput > dynamic_threshold):
            # If port is not already marked as above threshold, record the time
            if (dpid, port_no) not in self.above_threshold_time:
                self.above_threshold_time[(dpid, port_no)] = timestamp
            # If the port has been above threshold for longer than block window, block it
            elif timestamp - self.above_threshold_time[(dpid, port_no)] > self.block_window:
                # If port is not already blocked, log a warning and block the port
                if (dpid, port_no) not in self.blocked_ports:
                    self.logger.warning('Threshold exceeded on port %s of switch %s', port_no, dpid)
                    self._block_port(dpid, port_no)
                    self.blocked_ports[(dpid, port_no)] = timestamp  # Record the time when the port was blocked
                    self.below_threshold_time[(dpid, port_no)] = None  # Reset the below threshold timer
        else:
            # If port was marked as above threshold, remove the record
            if (dpid, port_no) in self.above_threshold_time:
                del self.above_threshold_time[(dpid, port_no)]
            # If port is currently blocked, track the time it remains below threshold
            if (dpid, port_no) in self.blocked_ports:
                if self.below_threshold_time.get((dpid, port_no)) is None:
                    self.below_threshold_time[(dpid, port_no)] = timestamp
                # If the port has been below threshold long enough, unblock it
                elif timestamp - self.below_threshold_time[(dpid, port_no)] > self.unlock_timeout:
                    del self.blocked_ports[(dpid, port_no)]
                    del self.below_threshold_time[(dpid, port_no)]
                    self._unblock_port(dpid, port_no)

            # Check if the port was recently unblocked and exceeds threshold again within 1 second
            if (dpid, port_no) in self.last_unblock_time and self.last_unblock_time[(dpid, port_no)] is not None:
                if timestamp - self.last_unblock_time[(dpid, port_no)] <= 1 and (rx_throughput > dynamic_threshold or tx_throughput > dynamic_threshold):
                    self.logger.warning('Threshold exceeded again on port %s of switch %s within 1 second of unblock', port_no, dpid)
                    self._block_port(dpid, port_no)
                    self.blocked_ports[(dpid, port_no)] = timestamp  # Record the time when the port was blocked

                    
    def _block_port(self, dpid, port_no):
        datapath = self.datapaths.get(dpid)
        if datapath is None:
            self.logger.error('Datapath %s not found', dpid)
            return
        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        match = parser.OFPMatch(in_port=port_no)
        actions = []  # Drop all packets
        self.add_flow(datapath, self.security_priority, match, actions)
        
        self.logger.info('\n---\n---\nBlocking port %s on switch %s\n---\n---\n', port_no, dpid)
        self.last_unblock_time[(dpid, port_no)] = None  # Reset last unblock time

    def _unblock_port(self, dpid, port_no):
        datapath = self.datapaths.get(dpid)
        if datapath is None:
            self.logger.error('Datapath %s not found', dpid)
            return
        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Match the specific rule we want to delete (i.e., the block rule)
        match = parser.OFPMatch(in_port=port_no)
        mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE_STRICT,  # Use DELETE_STRICT to delete specific flow
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=match,
            priority=self.security_priority  # Use the same priority as the block rule
        )
        datapath.send_msg(mod)
        
        self.logger.info('\n---\n---\nUnblocking port %s on switch %s\n---\n---\n', port_no, dpid)
        self.last_unblock_time[(dpid, port_no)] = time.time()  # Record the time when the port was unblocked


# Funzione principale
if __name__ == '__main__':
    from ryu.cmd import manager
    manager.main()
