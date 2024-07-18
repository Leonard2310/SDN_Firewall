# SDN_Firewall

## Overview
SDN_Firewall is a network security project designed to monitor and control incoming and outgoing traffic based on predefined rules within a Software-Defined Network (SDN) environment. It leverages a centralized controller to dynamically manage security rules, providing flexible and rapid responses to network threats such as Denial of Service (DoS) attacks.

## Features
- **Dynamic Rule Management**: Real-time programming and updating of firewall policies distributed to network devices.
- **Throughput Monitoring**: Periodic calculation of throughput to monitor network load and detect anomalies.
- **DoS Attack Mitigation**: Identification and blocking of traffic sources involved in DoS attacks.
- **Adaptive Traffic Control**: Automatic unblocking of previously blocked ports once normal traffic conditions resume.

## Implementation Details
The project is implemented using the Ryu SDN framework and includes the following key components:

### 1. SimpleSwitch13 Class Enhancement
The existing SimpleSwitch13 class is extended to create a controller capable of blocking DoS attacks:
- **Flow Entries Management**: Minimizes the number of packet-in events by installing flow entries to handle future packets.
- **MAC Address Learning**: Learns source MAC addresses and incoming ports, then forwards packets accordingly.

### 2. Throughput Calculation
The throughput is computed by periodically requesting statistics from each switch, using the formula:
\[ \text{Throughput} = \frac{\text{Current Bytes} - \text{Previous Bytes}}{\text{Current Timestamp} - \text{Previous Timestamp}} \]

### 3. Blocking and Unblocking Mechanisms
- **Dynamic Port Blocking**: Blocks ports experiencing excessive throughput indicative of a DoS attack.
- **Watchdog Timers**: Monitors blocked ports and unblocks them once normal conditions are detected.

### 4. Performance Evaluation
- **DoS Attack Simulation**: Evaluates the impact of DoS attacks on network performance and the effectiveness of mitigation strategies.
- **Bandwidth Utilization Analysis**: Visualizes average bandwidth utilization across different hosts during various communication scenarios.

## Getting Started

### Prerequisites
- Python 3.x
- Ryu SDN Framework
- Mininet Network Emulator

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Leonard2310/SDN_Firewall.git
   cd SDN_Firewall
   ```
   
2. Install required packages (TODO):
   ```bash
   pip install -r requirements.txt
   ```

### Usage
1. Start the Mininet topology (TODO):
   ```bash
   sudo mn --custom topo.py --topo mytopo --controller remote --mac --switch ovsk --link tc
   ```
2. Run the Ryu application(TODO):
   ```bash
   ryu-manager sdn_firewall.py
   ```

## Project Structure
- **sdn_firewall.py**: Main controller script for the SDN firewall.
- **topo.py**: Custom Mininet topology definition.
- **requirements.txt**: List of dependencies required for the project.
- **README.md**: Project documentation.

## Future Work
Future improvements to the SDN_Firewall project include:
- **Machine Learning Integration**: Dynamically adjust thresholds and enhance anomaly detection accuracy.
- **Advanced Metrics Analysis**: Expand traffic analysis to include packet loss and latency.
- **Fine-grained Policy Enforcement**: Implement application-level insights and user behavior-based policies.
- **Scalability Enhancements**: Optimize performance for larger networks.
- **Real-time Threat Intelligence**: Integrate threat intelligence feeds for proactive defense.
- **Compliance and Regulatory Standards**: Ensure alignment with data protection laws and security best practices.

## Contributors
- Leonardo Catello 
- Lorenzo Manco 

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
