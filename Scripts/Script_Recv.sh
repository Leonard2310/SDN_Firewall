#!/bin/bash

# Path to the packet capture file
PCAP_FILE="/home/so/Scrivania/Progetto_NCI/traffic_capture.pcap"

# Function to handle interruption (Ctrl+C)
cleanup() {
    echo "Interruption detected. Cleaning up and exiting..."

    # Stop the iperf server
    echo "Stopping the iperf server"
    pkill -f "iperf -s"

    # Stop tcpdump
    echo "Stopping tcpdump"
    pkill -f "tcpdump"

    exit 0
}

# Set the trap function to catch SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start the iperf server
echo "Starting the iperf server"
iperf -s &

# Start tcpdump to capture all UDP and TCP packets
echo "Starting tcpdump"
tcpdump -i h3-eth0 -w $PCAP_FILE &

# Wait for iperf to finish
wait
