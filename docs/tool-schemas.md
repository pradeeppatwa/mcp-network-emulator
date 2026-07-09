# Tool and Resource Schemas

## TOOLS

### 1. create_topology(config)
Backend: Both
Input: config dict with keys: type, hosts, switches, aps, stations
Output success: Topology created.
Output error: Invalid topology type. / Topology already active.

### 2. destroy_topology()
Backend: Both
Input: none
Output success: Topology destroyed.
Output error: No active topology to destroy.

### 3. set_delay(node1, node2, delay_ms)
Backend: Containernet
Input: node1:str, node2:str, delay_ms:int (>=0)
Output success: [delay_ms]ms delay set on [node1]<->[node2]
Output error: No active topology. / Node not found. / No link found.
API: node.connectionsTo(other)[0][0].config(delay=delay_ms)
Verified: Week 3 Day 3

### 4. set_bandwidth(node1, node2, bw_mbps)
Backend: Containernet
Input: node1:str, node2:str, bw_mbps:float (>0)
Output success: [bw_mbps]Mbps set on [node1]<->[node2]
Output error: No active topology. / Node not found. / bw_mbps must be > 0
API: node.connectionsTo(other)[0][0].config(bw=bw_mbps)
Verified: Week 3 Day 3

### 5. set_loss(node1, node2, loss_pct)
Backend: Containernet
Input: node1:str, node2:str, loss_pct:float (0-100)
Output success: [loss_pct]% loss set on [node1]<->[node2]
Output error: No active topology. / Node not found. / loss_pct must be 0-100
API: node.connectionsTo(other)[0][0].config(loss=loss_pct)
Verified: Week 3 Day 3

### 6. ping(src, dst)
Backend: Containernet
Input: src:str, dst:str
Output success: Ping [src]->[dst]: RTT min/avg/max ms
Output error: No active topology. / Node not found. / 100% packet loss
API: net.pingFull([src_node, dst_node])
Verified: Week 3 Day 5

### 7. run_iperf(src, dst)
Backend: Containernet
Input: src:str, dst:str
Output success: Iperf [src]->[dst]: tx transmit, rx receive
Output error: No active topology. / Node not found. / iperf not installed
API: net.iperf((src_node, dst_node))
Known constraint: requires iperf+telnet in container image
Verified: Week 3 Day 5

### 8. set_channel(ap, channel)
Backend: Mininet-WiFi
Input: ap:str, channel:int (1-13)
Output success: Channel [channel] set on [ap]
Output error: No active topology. / AP not found. / channel must be 1-13
API: ap.cmd hostapd_cli chan_switch
Frequency: freq = 2407 + channel x 5
Verified: Week 4 Day 4

## RESOURCES

### topology://nodes
Backend: Both
Output: Hosts/Switches/APs/Stations list
API: net.hosts, net.switches, net.aps, net.stations

### topology://links
Backend: Containernet
Output: [node1]<->[node2] delay/bw/loss
API: node.connectionsTo(other)

### topology://links/wifi
Backend: Mininet-WiFi
Output: station -> ap: signal dBm channel
API: ap.cmd iw station dump

### topology://routing/{node}
Backend: Containernet
Output: ip route filtered, removes Docker 172.17.0.0/16 route
API: node.cmd ip route

### topology://wifi/{ap}
Backend: Mininet-WiFi
Output: AP channel, station signal/rate
API: ap.cmd iw station dump

## GUARD FUNCTION

def require_active_topology():
    if net is None:
        raise ValueError(No active topology. Call create_topology() first.)

## PROMPTS

### link_impairment_test
Already in server.py - Week 2

### wifi_channel_test(ap, rssi_threshold=-70)
Check signal on [ap]. If RSSI below [threshold]dBm, switch to channel 11.
