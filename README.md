# SDN_Firewall

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Implementation Details](#implementation-details)
    1. [SimpleSwitch13 Class Enhancement](#1-simpleswitch13-class-enhancement)
    2. [Throughput Calculation](#2-throughput-calculation)
    3. [Blocking and Unblocking Mechanisms](#3-blocking-and-unblocking-mechanisms)
    4. [Performance Evaluation](#4-performance-evaluation)
4. [Implementation Steps](#implementation-steps)
    1. [Introduction](#introduction)
    2. [Objectives](#objectives)
    3. [DoS Attack Implementation](#dos-attack-implementation)
        1. [Final Mininet Topology](#final-mininet-topology)
    4. [Performance Evaluation](#performance-evaluation)
    5. [Conclusion](#conclusion)
5. [Getting Started](#getting-started)
    1. [Prerequisites](#prerequisites)
6. [Future Work](#future-work)
7. [Contributors](#contributors)
8. [License](#license)

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
The throughput is computed by periodically requesting statistics from each switch.

### 3. Blocking and Unblocking Mechanisms
- **Dynamic Port Blocking**: Blocks ports experiencing excessive throughput indicative of a DoS attack.
- **Watchdog Timers**: Monitors blocked ports and unblocks them once normal conditions are detected.

### 4. Performance Evaluation
- **DoS Attack Simulation**: Evaluates the impact of DoS attacks on network performance and the effectiveness of mitigation strategies.
- **Bandwidth Utilization Analysis**: Visualizes average bandwidth utilization across different hosts during various communication scenarios.

## Implementation Steps

### Introduction
Ensuring the reliability and availability of services in network and cloud infrastructures is crucial. This project focuses on understanding, implementing, and mitigating Denial of Service (DoS) attacks within a simulated network environment. A DoS attack aims to make a network service unavailable by overwhelming it with illegitimate traffic, causing significant disruption for legitimate users. Studying DoS attacks helps develop effective strategies to detect, mitigate, and prevent such threats, thus maintaining the integrity and performance of network infrastructures.

Software-Defined Networking (SDN) offers an innovative approach to network management by separating the control plane from the data plane, allowing centralized, programmable control of the network. This dynamic and automated network configuration can counteract DoS attacks effectively. Using SDN controllers like Ryu, network administrators can monitor traffic in real-time, identify abnormal patterns indicative of an attack, and deploy mitigation strategies promptly and effectively.

### Objectives
The primary objectives of this project are twofold:

1. **Develop a Monitoring System**: Create a robust system capable of detecting abnormal traffic patterns indicative of a DoS attack.
2. **Implement Mitigation Mechanisms**: Develop automated mechanisms to safeguard network operations for legitimate users.

The project involves defining a specific network topology in Mininet, generating both normal and DoS traffic, and evaluating the network's performance under these conditions. Additionally, the project aims to utilize the Ryu controller to monitor traffic, detect excessive traffic patterns, and apply OpenFlow rules to block malicious traffic, ensuring the network remains functional for legitimate users.

### DoS Attack Implementation

#### Final Mininet Topology
A specific network topology was developed using Python scripts with the Mininet library. The topology includes hosts and switches configured to simulate both common and DoS traffic. Host H1 acts as the attacker generating malicious traffic, while H2 generates normal traffic, both targeting H3, the receiver. The topology is designed to test the network's performance and resilience against DoS attacks.

The final implementation involves the following components:
- **Dos Host (H1)**: Generating both normal and DoS traffic.
- **Hosts (H2, H3, H4)**: Generatic normal traffic.
- **Switches (S1, S2, S3, S4)**: Managing network traffic.
- **Controller (C)**: Overseeing the network operations and enforcing OpenFlow rules.

A Python script creates these network components, establishes connections, and configures the desired network structure.

### Performance Evaluation
The performance evaluation involves monitoring the network behavior over time. Initially, hosts share bandwidth, but during a DoS attack initiated by H1, the network responds by blocking H1 and redistributing the available bandwidth. The dynamic response is facilitated by the SDN Firewall's advanced blocking and unblocking mechanisms and watchdog timers. Following the cessation of the DoS attack, H1 is unblocked, restoring normal network operations.

### Conclusion
The final implementation of the SDN Firewall solution is robust against DoS attack congestion while accommodating regular traffic. Through iterative testing and enhancements, the solution effectively distinguishes between malicious and benign traffic patterns, dynamically adjusting thresholds based on real-time conditions. Future proposals for the project include integrating machine learning for better anomaly detection, expanding traffic analysis metrics, and implementing fine-grained policy enforcement based on user behaviors.

## Getting Started

### Prerequisites
- Python 3.x
- Ryu SDN Framework
- Mininet Network Emulator

## Future Work
Future improvements to the SDN_Firewall project include:
- **Machine Learning Integration**: Dynamically adjust thresholds and enhance anomaly detection accuracy.
- **Advanced Metrics Analysis**: Expand traffic analysis to include packet loss and latency.
- **Fine-grained Policy Enforcement**: Implement application-level insights and user behavior-based policies.
- **Scalability Enhancements**: Optimize performance for larger networks.
- **Real-time Threat Intelligence**: Integrate threat intelligence feeds for proactive defense.
- **Compliance and Regulatory Standards**: Ensure alignment with data protection laws and security best practices.

## Contributors
- [Leonardo Catello](https://github.com/Leonard2310)
- [Lorenzo Manco](https://github.com/Rasbon99)

## License
This project is licensed under the [GNU AFFERO General Public License](LICENSE). Refer to the LICENSE file for more information.