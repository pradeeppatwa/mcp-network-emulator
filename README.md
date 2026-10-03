# MCP Server for Containernet and Mininet-WiFi

A natural language interface for network emulation — control and measure real network topologies using plain English through VS Code Copilot.

---

## What is this?

This project builds a Model Context Protocol (MCP) server that connects AI clients (VS Code Copilot or Claude Desktop) to Containernet and Mininet-WiFi network emulation environments. Instead of writing Python scripts or running CLI commands manually, a researcher describes what they want in natural language and the AI automatically calls the right tools, executes the network operation, and reports the result.

This is believed to be the first integration of MCP with Containernet and Mininet-WiFi network emulation environments.

---

## Architecture

Three-layer architecture:

- **Layer 1 — AI Client:** VS Code Copilot or Claude Desktop. Accepts natural language input and autonomously issues MCP tool calls.
- **Layer 2 — MCP Server:** server.py exposes 10 tools, 3 resources, and 2 prompts via JSON-RPC 2.0 over stdio transport.
- **Layer 3 — Unified Backend:** ramonfontes/containernet manages Docker hosts, OVS switches, WiFi stations, and access points in one process.

See [docs/architecture.md](docs/architecture.md) for full details.

---

## Prerequisites

- Ubuntu 24.04 LTS
- Python 3.12
- Docker
- Open vSwitch (OVS)
- ramonfontes/containernet installed and on PYTHONPATH
- VS Code with GitHub Copilot extension
- Custom Docker image: mcp-network-node

---

## Quick Start

```bash
sudo modprobe mac80211_hwsim radios=4
cd mcp-network-emulator && source venv/bin/activate
sudo python3 server.py
```

VS Code Copilot connects automatically via `.vscode/mcp.json`.

Example prompt: `"Create a wired topology with 2 hosts and ping h1 to h2"`

---

## Evaluation Results

All 11 use cases verified through VS Code Copilot Agent Mode using natural language prompts only. No manual CLI commands used.

| Use Case | Description | Result |
|----------|-------------|--------|
| UC1a | Basic wired ping | RTT = 2.0ms ✅ |
| UC1b | Delay on host interfaces | RTT = 205ms ✅ |
| UC1c | Delay on switch-to-switch link | RTT = 205ms ✅ |
| UC1d | Bandwidth + loss + routing table | All verified ✅ |
| UC1e | Multi-switch iperf throughput | 10.8 Gbps ✅ |
| UC2a | WiFi RSSI check, no channel change | Conditional reasoning correct ✅ |
| UC2b | WiFi channel switch 1→11 | Stations remain connected ✅ |
| UC2c | Multi-station wireless iperf | 7.92 Mbits/sec ✅ |
| UC2d | Multi-AP station inventory | 2 stations per AP correct ✅ |
| UC3a | Hybrid iperf wired→wireless | 1.22 Gbits/sec ✅ |
| UC3b | Hybrid cross-segment delay | RTT 5ms → 102ms ✅ |
| UC4 | IEEE 802.11s mesh topology | RTT = 0.269ms ✅ |

See [docs/evaluation.md](docs/evaluation.md) for full results and prompts.

---

## Project Structure

```
mcp-network-emulator/
├── server.py              # MCP server — all 10 tools, 3 resources, 2 prompts
├── Dockerfile             # Custom Docker image (mcp-network-node)
├── .vscode/mcp.json       # VS Code Copilot MCP configuration
├── tests/
│   └── test_all_tools.py  # Verification script for all tools
└── docs/
    ├── architecture.md    # System architecture and technical decisions
    ├── tools.md           # Tool and resource reference
    └── evaluation.md      # Use case results and latency observations
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | Three-layer architecture, MCP flow, key decisions |
| [Tools Reference](docs/tools.md) | All 10 tools, 3 resources, 2 prompts with examples |
| [Evaluation](docs/evaluation.md) | All 11 use case results with prompts and measurements |

---

## Project Info

**Student:** Pradeep Patwa
**Programme:** M.Eng. Information Technology — Semester 3
**University:** Frankfurt University of Applied Sciences
**Supervisor:** Prof. Dr. Armin Lehmann
**Duration:** 22-week Individual Project (5 credits)
