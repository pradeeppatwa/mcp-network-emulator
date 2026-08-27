# MCP Server for Containernet and Mininet-WiFi

A Model Context Protocol (MCP) server that enables AI clients (VS Code Copilot, Claude Desktop) to control network emulation environments through natural language.

## Project

**Title:** Design, Implementation and Evaluation of an MCP-Server for Containernet and Mininet-WiFi
**University:** Frankfurt University of Applied Sciences
**Programme:** Master of Engineering - Information Technology
**Supervisor:** Prof. Dr. Armin Lehmann

## What it does

Instead of manually writing Python scripts or CLI commands to control emulated networks, you simply describe what you want in natural language. The AI client calls the appropriate MCP tools automatically.

Example prompt:
Create a hybrid topology with 3 hosts and a WiFi AP, run iperf between h1 and h3, report throughput

The MCP server handles topology creation, link configuration, traffic measurement, and WiFi management from one natural language prompt.

## Architecture

Three-layer architecture:
- Layer 1 - AI Client: VS Code Copilot / Claude Desktop
- Layer 2 - MCP Server: server.py - exposes tools, resources, prompts via JSON-RPC 2.0 over stdio
- Layer 3 - Unified Backend: ramonfontes/containernet (Docker + Mininet-WiFi combined)

## Tools (10)

| Tool | Description |
|---|---|
| create_topology | Create wired, wireless, or hybrid topology |
| destroy_topology | Stop and clean up active topology |
| set_delay | Apply link delay via tc netem |
| set_bandwidth | Limit link bandwidth |
| set_loss | Inject packet loss |
| ping | Measure RTT between nodes |
| run_iperf | Measure TCP throughput |
| set_channel | Change WiFi AP channel |
| get_routing_table | Read node routing table |
| get_wifi_stats | Read AP WiFi statistics and RSSI |

## Resources (3)

- topology://nodes - List all nodes
- topology://links - List wired links
- topology://links/wifi - List wireless associations

## Requirements

- Ubuntu 24.04
- Docker
- ramonfontes/containernet
- mac80211_hwsim kernel module
- Python 3.12
- MCP SDK
- VS Code with GitHub Copilot extension

## Setup

Load wireless kernel module:
sudo modprobe mac80211_hwsim radios=4

Start MCP server:
sudo python3 server.py

Configure VS Code Copilot by opening this project folder. The .vscode/mcp.json file configures the MCP server connection automatically.

## Docker Image

A custom Docker image is provided with iperf and telnet pre-installed:
docker build -t mcp-network-node .

## Evaluation Results

All three use cases verified through VS Code Copilot Agent Mode:

| Use Case | Result |
|---|---|
| Wired link impairment + ping | RTT = 2.0ms, 0% loss |
| WiFi channel optimisation | RSSI read, conditional channel switch |
| Hybrid topology + iperf | Wired 14.1 Gbps, Wireless 18.6 Gbps |

Position-based RSSI confirmed: moving a station to position (100,100) caused RSSI to drop from -40 dBm to -72 dBm.

## Licence

MIT
