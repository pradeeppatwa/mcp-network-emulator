# Evaluation Results

---

## Evaluation Approach

All 11 use cases were evaluated exclusively through VS Code Copilot Agent Mode
using natural language prompts. No manual CLI commands, Python scripts, or
direct API calls were used during evaluation. The AI client autonomously
selected the appropriate MCP tools, determined the correct sequence of calls,
and interpreted the results — demonstrating the core objective of the project.

**Environment:** Ubuntu 24.04.4 LTS, single machine

**Backend:** ramonfontes/containernet

**AI Client:** VS Code Copilot Agent Mode (GitHub Copilot Free)

---

## Use Case Results

### UC1a — Basic Wired Topology and Ping

**Prompt:** "Create a wired topology with 2 hosts and 1 switch, then ping from h1 to h2."

**Topology:** h1, h2, s1

**Result:** RTT = 2.0ms, 0% packet loss

**Status:** ✅ PASS

---

### UC1b — Wired Delay on Host Interfaces

**Prompt:** "Create a topology with two switches and two hosts. Apply 50ms delay on h1-s1 and h2-s2. Ping from h1 to h2 and confirm RTT reflects the delay."

**Topology:** h1, h2, s1, s2

**Result:** RTT = 205ms, 0% packet loss

**Status:** ✅ PASS

---

### UC1c — Wired Delay on Switch-to-Switch Link

**Prompt:** "Create a topology with two switches and two hosts. Add 100ms delay on the link between s1 and s2. Ping from h1 to h2 and tell me if the round-trip time reflects that delay."

**Topology:** h1, h2, s1, s2

**Result:** RTT = 205ms, 0% packet loss

**Status:** ✅ PASS

---

### UC1d — Combined Link Impairment

**Prompt:** "Create a wired topology with 2 hosts and 1 switch. Set 100Mbps bandwidth and 5% packet loss on h1-s1. Ping from h1 to h2 and show the routing table of h1."

**Topology:** h1, h2, s1

**Result:** Bandwidth limited, 5% loss applied, routing table returned correctly

**Status:** ✅ PASS

---

### UC1e — Multi-Switch Wired Throughput

**Prompt:** "Create a topology with 4 hosts across 2 switches. Run iperf between h1 and h3 and report the throughput."

**Topology:** h1, h2, h3, h4, s1, s2

**Result:** Throughput = 10.8 Gbps

**Status:** ✅ PASS

---

### UC2a — WiFi Signal Check, No Channel Change Needed

**Prompt:** "Create a topology with one access point and two stations. Check signal strength. If any station RSSI is below -70dBm switch the channel."

**Topology:** ap1, sta1, sta2

**Result:** sta1 = -36dBm, sta2 = -36dBm. AI correctly decided NOT to switch channel — demonstrating conditional reasoning based on RSSI threshold.

**Status:** ✅ PASS

---

### UC2b — WiFi Channel Switch Verification

**Prompt:** "Create a wireless topology with one AP and two stations. Check WiFi channel and signal strength. Switch ap1 to channel 11 and verify stations remain connected."

**Topology:** ap1, sta1, sta2

**Result:** Channel switched 1→11, both stations remain connected at -36dBm

**Status:** ✅ PASS

---

### UC2c — Multi-Station Wireless Throughput

**Prompt:** "Create a wireless topology with one AP and three stations. Run iperf between sta1 and sta2, then sta1 and sta3. Compare throughput."

**Topology:** ap1, sta1, sta2, sta3

**Result:** sta1→sta2 = 7.92 Mbits/sec, sta1→sta3 = 7.92 Mbits/sec

**Status:** ✅ PASS

---

### UC2d — Multi-AP Inventory

**Prompt:** "Create a wireless topology with two APs and four stations, two per AP. Check WiFi stats on both APs and summarise which stations are connected to which AP and their signal strength."

**Topology:** ap1, ap2, sta1, sta2, sta3, sta4

**Result:** sta1+sta3 on ap1, sta2+sta4 on ap2, all at -36dBm

**Status:** ✅ PASS

---

### UC3a — Hybrid Topology Throughput

**Prompt:** "Create a hybrid topology with two wired hosts on a switch and one AP with one station. Run iperf between h1 and sta1 and report throughput."

**Topology:** h1, h2, s1, ap1, sta1

**Result:** Throughput = 1.22 Gbits/sec

**Status:** ✅ PASS

---

### UC3b — Hybrid Topology Cross-Segment Delay

**Prompt:** "Create a hybrid topology. Ping h1 to sta1 for baseline RTT. Add 100ms delay on h1-s1. Ping again and confirm the RTT increased."

**Topology:** h1, h2, s1, ap1, sta1

**Result:** Baseline RTT = 5.268ms → After delay = 102.398ms

**Status:** ✅ PASS

---

### UC4 — IEEE 802.11s Mesh Topology

**Prompt:** "Create a mesh topology with three wireless mesh nodes. Confirm that traffic can flow between sta1 and sta3 through the mesh network."

**Topology:** sta1, sta2, sta3 (IEEE 802.11s, channel 5, ssid meshNet)

**Result:** Ping sta1→sta3: RTT = 0.269ms, 0% packet loss

**Status:** ✅ PASS

---

## Summary

| Category | Use Cases                     | Result      |
|----------|-------------------------------|-------------|
| Wired    | UC1a, UC1b, UC1c, UC1d, UC1e | 5/5 ✅      |
| Wireless | UC2a, UC2b, UC2c, UC2d       | 4/4 ✅      |
| Hybrid   | UC3a, UC3b                   | 2/2 ✅      |
| Mesh     | UC4                          | 1/1 ✅      |
| **Total**| **11 use cases**             | **11/11 ✅** |

---

## Latency Observations

Approximate measurements on a single Ubuntu 24.04 machine.

| Operation                            | Approximate Latency                          |
|--------------------------------------|----------------------------------------------|
| create_topology (wired)              | ~5 seconds                                   |
| create_topology (wireless)           | ~15 seconds (includes WiFi association wait) |
| create_topology (hybrid)             | ~20 seconds                                  |
| create_topology (mesh)               | ~12 seconds                                  |
| destroy_topology                     | ~3 seconds                                   |
| set_delay / set_bandwidth / set_loss | ~1-2 seconds                                 |
| ping                                 | ~2 seconds                                   |
| run_iperf                            | ~8 seconds                                   |
| set_channel                          | ~1 second                                    |
| get_routing_table / get_wifi_stats   | ~1 second                                    |
