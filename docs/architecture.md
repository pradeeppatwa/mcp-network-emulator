# MCP Server Architecture
## Project: MCP Server for Containernet and Mininet-WiFi

## 1. Overview
Three-layer architecture:
- Layer 1: AI Client — Claude Desktop or VS Code Copilot
- Layer 2: MCP Server — server.py, exposes tools/resources/prompts via JSON-RPC 2.0 over stdio
- Layer 3: Emulation Backends — Containernet (wired) and Mininet-WiFi (wireless), managed in-process

## 2. Backend Management
Pattern: In-process, single active backend.
server.py runs as root and imports both backends directly.
Two global state variables:
  net = None
  active_backend = None
Only one backend active at a time.
Rationale: Simpler, faster to implement, sufficient for a single-user research prototype.

## 3. Topology Lifecycle
States: IDLE -> create_topology() -> ACTIVE -> destroy_topology() -> IDLE
- Startup: lazy, only when create_topology() is called
- Active: all tools operate here
- Teardown: explicit destroy_topology() or server exit
Error in IDLE: "No active topology. Call create_topology() first."

## 4. Tool-to-Backend Mapping

TOOLS (state-changing or active measurement):

  create_topology(config)        | Both          | net.start() / net.build()
  destroy_topology()             | Both          | net.stop()
  set_delay(node1,node2,ms)      | Containernet  | node.connectionsTo()[0][0].config(delay=...)
  set_bandwidth(node1,node2,bw)  | Containernet  | node.connectionsTo()[0][0].config(bw=...)
  set_loss(node1,node2,pct)      | Containernet  | node.connectionsTo()[0][0].config(loss=...)
  ping(src,dst)                  | Containernet  | net.pingFull([src_node, dst_node])
  run_iperf(src,dst)             | Containernet  | net.iperf((src_node, dst_node))
  set_channel(ap,channel)        | Mininet-WiFi  | ap.cmd('hostapd_cli chan_switch 1 freq')

RESOURCES (read-only, no state change):

  topology://nodes               | Both          | net.hosts, net.switches, net.aps
  topology://links               | Containernet  | node.connectionsTo()
  topology://links/wifi          | Mininet-WiFi  | ap.cmd('iw dev ... station dump')
  topology://routing/{node}      | Containernet  | node.cmd('ip route')
  topology://wifi/{ap}           | Mininet-WiFi  | ap.cmd('iw dev ... station dump')

Rationale: Tools cause state changes or active traffic. Resources only read existing state.

## 5. Error Handling

Three categories:
1. No active topology: "No active topology. Call create_topology() first."
2. Invalid arguments: "Node 'h5' not found. Available nodes: h1, h2, h3, s1"
3. Backend failure: "Backend error: [specific error message]"

## 6. Project Structure

  server.py                      # MCP server entry point
  backends/containernet_backend.py
  backends/mininet_wifi_backend.py
  tools/wired.py                 # set_delay, set_bandwidth, set_loss, ping, run_iperf
  tools/wireless.py              # set_channel
  resources/topology.py          # list_nodes, list_links, routing, wifi stats
  topologies/use_case_1.py       # Wired topology
  topologies/use_case_2.py       # Wireless topology
  topologies/use_case_3.py       # Hybrid topology
  docs/                          # Documentation
  tests/                         # Evaluation scripts

## 7. Architecture Diagram

  [AI CLIENT]
  Claude Desktop / VS Code Copilot
         |
         | MCP Protocol (stdio, JSON-RPC 2.0)
         |
  [MCP SERVER - server.py - runs as root]
  Tools: set_delay, set_bandwidth, set_loss,
         ping, run_iperf, set_channel,
         create_topology, destroy_topology
  Resources: topology://nodes, topology://links,
             topology://routing/{node}, topology://wifi/{ap}
  Prompts: link_impairment_test, wifi_channel_test
         |
         | Direct Python calls (in-process)
         |
    _____|_____
   |           |
[CONTAINERNET] [MININET-WIFI]
Docker hosts   mac80211_hwsim
OVS switches   hostapd/wmediumd
tc netem       Wireless APs/stations
