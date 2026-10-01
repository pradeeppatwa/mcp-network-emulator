# Tools, Resources and Prompts Reference
## Project: MCP Server for Containernet and Mininet-WiFi

---

## Tools

All tools require an active topology. Call `create_topology` first.

| Tool              | Parameters                                    | Returns                              |
|-------------------|-----------------------------------------------|--------------------------------------|
| create_topology   | topology_type, hosts, switches, aps, stations | Topology created (type): nodes...    |
| destroy_topology  | —                                             | Topology destroyed successfully.     |
| set_delay         | node1, node2, delay_ms (int, >=0)             | Xms delay set on link node1<->node2. |
| set_bandwidth     | node1, node2, bw_mbps (float, >0)             | XMbps bandwidth set on link...       |
| set_loss          | node1, node2, loss_pct (float, 0-100)         | X% packet loss set on link...        |
| ping              | src, dst                                      | RTT min/avg/max = Xms, Y% loss.      |
| run_iperf         | src, dst                                      | Iperf src->dst: throughput = X       |
| set_channel       | ap, channel (int, 1-13)                       | Channel X set on ap (freq: YMHz).    |
| get_routing_table | node                                          | Routing table for node: ip routes    |
| get_wifi_stats    | ap                                            | AP ap1 | Channel: X | stations...    |

---

## Resources

Read-only. Do not change network state.

| URI                   | Returns                                                    |
|-----------------------|------------------------------------------------------------|
| topology://nodes      | All nodes grouped by type (hosts, switches, APs, stations) |
| topology://links      | All wired links — e.g. h1<->s1, h2<->s1                   |
| topology://links/wifi | WiFi station associations per AP with RSSI                 |

---

## Prompts

Reusable templates that guide the AI toward a structured experiment workflow.

| Prompt               | Parameters                              | Purpose                                          |
|----------------------|-----------------------------------------|--------------------------------------------------|
| link_impairment_test | node1, node2, host1, host2, delay_ms=50 | Apply delay and verify with ping                 |
| wifi_channel_test    | ap, rssi_threshold=-70                  | Check RSSI and switch channel if below threshold |

---

## Notes

**set_delay on switch-to-switch links:**
When both nodes are OVS switches, delay is applied on host-facing interfaces
instead. OVS kernel datapath bypasses tc netem on switch interfaces.
RTT correctly reflects the configured delay.

**run_iperf:**
Uses direct node.cmd() approach instead of net.iperf(). net.iperf() hangs
with Docker nodes due to telnet coordination issues.

**get_wifi_stats channel:**
Reads channel from ap.wintfs[0].channel which reflects runtime state.
ap.params["channel"] becomes stale after set_channel() is called.
