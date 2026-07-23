# Evaluation Metrics
## Project: MCP Server for Containernet and Mininet-WiFi

Evaluation covers three dimensions: correctness, latency, and use case coverage.
Measurements taken during Weeks 16-18 (Phase 4: Testing and Evaluation).

## Evaluation Dimensions

1. Correctness: Did the tool produce the expected network effect?
   Verified by reading actual network state after each tool call.

2. Tool Call Latency: Time from MCP tools/call request to response.
   Measured using MCP Inspector History timestamps or Python time.time().

3. End-to-End Use Case Correctness: Did the AI complete the full use case
   from a single natural language prompt? Binary: pass or fail.

## Per-Tool Evaluation

Tool               | Correctness Check                              | Target Latency
create_topology    | Nodes appear in topology://nodes               | < 10s
destroy_topology   | net.stop() completes, docker ps -a empty       | < 5s
set_delay          | RTT increases by ~delay_ms after call          | < 2s
set_bandwidth      | iperf throughput capped at bw_mbps             | < 2s
set_loss           | ping shows ~loss_pct packet loss               | < 2s
ping               | Returns real RTT matching network conditions    | < 5s
run_iperf          | Returns real throughput matching link config    | < 15s
get_routing_table  | Returns correct ip route for that node         | < 2s
get_wifi_stats     | Returns real RSSI from iw station dump         | < 2s
set_channel        | iw info confirms channel changed               | < 3s

## Use Case 1 - Link Impairment and Verification (Wired)

Prompt: Add 50ms delay on s1-s2, ping h1 to h2, confirm RTT increased.

Steps AI must perform:
1. Call set_delay(s1, s2, 50)
2. Call ping(h1, h2)
3. Confirm RTT increased by approximately 50ms

Correctness: PASS if RTT after > RTT before + 40ms (10ms tolerance)
Method: Run 5 times, record baseline RTT before and after, compare.

## Use Case 2 - WiFi Channel Optimisation (Wireless)

Prompt: Check RSSI on ap1. If any station below -70dBm, switch to channel 11.

Steps AI must perform:
1. Call get_wifi_stats(ap1)
2. Evaluate RSSI against -70dBm threshold
3. Conditionally call set_channel(ap1, 11)
4. Call get_wifi_stats(ap1) again to verify

Correctness: PASS if AI correctly evaluates threshold AND acts conditionally.
Method: Place one station below threshold, one above. Run 5 times.

## Use Case 3 - Topology Creation and Benchmarking (Hybrid)

Prompt: Create 3 Docker hosts on a switch with a WiFi AP and 2 stations,
run iperf between h1 and h3, report throughput.

Steps AI must perform:
1. Call create_topology with hybrid config
2. Verify nodes via topology://nodes
3. Call run_iperf(h1, h3)
4. Report throughput result

Correctness: PASS if topology created and iperf returns real throughput.
Method: Run 5 times, record pass/fail and throughput values.

## Additional Use Cases

Use Case 4: Set 100ms delay AND 10% loss on s1-s2, ping, report combined effect.
Use Case 5: Show routing table of h1 and explain the default route.
Use Case 6: List all nodes and links in the current topology.

## Evaluation Summary

Metric                        | Target
Per-tool correctness          | 100% for all 10 tools
Use Case 1 pass rate          | >= 4/5 runs
Use Case 2 pass rate          | >= 4/5 runs
Use Case 3 pass rate          | >= 4/5 runs
Tool call latency average     | < 5s for all tools
End-to-end use case latency   | < 30s per use case
