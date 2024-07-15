#!/bin/bash

# Settings
DESTINATION_IP="10.0.0.3"
TIME=60  # Duration of data transfer in seconds
DESTINATION_PORT=5201  # Destination port for the iperf server

# BW = 3 Mbit/s
# Ping = 100ms = RTT
# Window Size = BW * RTT = 0.3 Mbit = 38 Kbytes
WS=19K  # TCP WS will be doubled upon execution

# Function to handle interruption (Ctrl+C)
cleanup() {
    echo "Transfer finished."
    # Terminate all iperf instances that were started
    kill ${PID1} ${PID2} ${PID3} >/dev/null 2>&1
    exit 0
}

# Set the trap function to catch SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start data transfer with iperf in TCP mode - Session 1
echo "Starting data transfer with iperf in TCP mode (Session 1)..."
iperf -c $DESTINATION_IP -w $WS -t $TIME -i 1 &
PID1=$!

# Wait for Session 1 to complete before continuing
wait ${PID1}
echo "Session 1 completed."

# Start data transfer with iperf in TCP mode - Session 2
echo "Starting data transfer with iperf in TCP mode (Session 2)..."
iperf -c $DESTINATION_IP -w $WS -t $TIME -i 1 &
PID2=$!

# Wait for Session 2 to complete before continuing
wait ${PID2}
echo "Session 2 completed."

# Start data transfer with iperf in TCP mode - Session 3
echo "Starting data transfer with iperf in TCP mode (Session 3)..."
iperf -c $DESTINATION_IP -w $WS -t $TIME -i 1 &
PID3=$!

# Wait for Session 3 to complete before continuing
wait ${PID3}
echo "Session 3 completed."

echo "All transfers are completed."
