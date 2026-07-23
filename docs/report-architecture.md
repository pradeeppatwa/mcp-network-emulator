# Architecture Section - Final Report Draft
## Project: MCP Server for Containernet and Mininet-WiFi

---

## 3. Architecture

### 3.1 Overview

The MCP server follows a three-layer architecture connecting AI clients to a
unified network emulation backend through the Model Context Protocol.

Layer 1 - AI Client: Claude Desktop or VS Code Copilot Agent Mode. The user
interacts through natural language. The AI client reads the server's registered
tools and resources, decides which to call based on the user's request, and
sends structured JSON-RPC 2.0 tool calls to the MCP server.

Layer 2 - MCP Server (server.py): The central component of this project.
Exposes eight tools, five resources, and two prompt templates to the AI client
via the stdio transport. Runs as root to satisfy the emulation backend's
privilege requirements. Translates AI tool calls into direct Python API calls
against the emulation backend.

Layer 3 - Unified Emulation Backend (ramonfontes/containernet): A fork of
Mininet that combines Containernet Docker host support with Mininet-WiFi
wireless capabilities in a single backend. One Containernet net object manages
Docker hosts, Docker WiFi stations, wired OVS switches, and wireless access
points simultaneously.

### 3.2 Backend Selection Rationale

The initial architecture considered two separate backends - Containernet for
the wired backbone and Mininet-WiFi for the wireless edge - coordinated by
the MCP server. This was revised following supervisor feedback to use a single
unified backend (ramonfontes/containernet) that handles both wired and wireless
emulation in one Python process. This simplifies the architecture significantly:
no backend switching logic, no port conflicts between two separate OVS
controllers, and a single net.start() call to initialise the entire topology.

### 3.3 MCP Primitive Selection

Tools were chosen for operations that cause state changes or generate active
network traffic: set_delay, set_bandwidth, set_loss, ping, run_iperf,
set_channel, create_topology, and destroy_topology. Resources were chosen for
read-only state queries with no side effects: topology://nodes, topology://links,
topology://links/wifi, topology://routing/{node}, and topology://wifi/{ap}.
This distinction follows the MCP specification's own definitions and was
verified through hands-on implementation in the development phase.

### 3.4 Topology Lifecycle

The server maintains a single global net variable. On startup, net is None
and the server is in IDLE state. The AI client must call create_topology()
first, which starts the emulation backend and transitions the server to ACTIVE
state. All other tools require ACTIVE state - calling them in IDLE returns a
clean error message rather than a Python exception. The destroy_topology() tool
stops the backend and returns the server to IDLE state. This lifecycle is also
triggered on server shutdown to ensure clean cleanup of Docker containers and
OVS bridges.

### 3.5 Error Handling

Three error categories are handled explicitly. First, state errors when tools
are called before a topology exists - these return a clear message directing
the AI to call create_topology() first. Second, argument errors when node names
do not exist in the active topology or parameter values are out of range -
these return a message listing available nodes. Third, backend errors when the
emulation itself fails - these propagate the underlying error message wrapped
in a structured MCP error response. Structural validation (missing required
parameters, wrong types) is handled automatically by FastMCP using Pydantic,
as verified during the development phase.

### 3.6 Architecture Diagram

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
             topology://links/wifi,
             topology://routing/{node},
             topology://wifi/{ap}
  Prompts: link_impairment_test, wifi_channel_test
         |
         | Direct Python API calls (in-process)
         |
  [UNIFIED BACKEND - ramonfontes/containernet]
  Docker hosts (cls=Docker)
  Docker WiFi stations (cls=DockerSta)
  OVS switches
  WiFi access points
  tc netem (delay/bandwidth/loss)
  hostapd / wmediumd (wireless)
  mac80211_hwsim (virtual WiFi radios)
