import sys
import os
import subprocess
import time
import json
import functools
import inspect
import re

# Ensure containernet-wifi is findable when running as root
sys.path.insert(0, '/home/pradeepp/pradeep/containernet-wifi')

from mcp.server.fastmcp import FastMCP

# Backend imports at module level
try:
    from containernet.net import Containernet
    from containernet.node import Docker, DockerSta
    from containernet.link import TCLink
    from mininet.node import Controller
    from mininet.log import setLogLevel
    setLogLevel("warning")
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    # stdout carries the MCP protocol messages, so diagnostics go to stderr
    print(f"Warning: Backend not available: {e}", file=sys.stderr)

# ─────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────

net = None  # live Containernet net object

def require_active_topology():
    """Guard function — every tool calls this first."""
    if net is None:
        raise ValueError("No active topology. Call create_topology() first.")

mcp = FastMCP("network-emulator")

# Traffic-control settings that are active on each interface, stored by interface name.
# Mininet deletes all rules of an interface whenever config() is called and rebuilds
# only what that call asks for. Every tool that changes one setting therefore stores it
# here and re-applies all settings of the interface together.
iface_state = {}

def apply_tc(intf, **changes):
    """Store the new setting(s) of an interface and re-apply all of its settings."""
    state = iface_state.setdefault(intf.name, {})
    state.update(changes)
    bw, delay, loss = state.get("bw"), state.get("delay"), state.get("loss")
    if bw is None and not delay and not loss:
        intf.tc("%s qdisc del dev %s root")   # nothing left to apply: remove all rules
        return
    intf.config(bw=bw,
                delay=None if delay is None else f"{delay}ms",
                loss=loss)

# ─────────────────────────────────────────
# CALL LOG
# ─────────────────────────────────────────

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "calls.jsonl")

def logged(tool):
    """Append one JSON line per tool call (name, arguments, status, duration, result)."""
    @functools.wraps(tool)
    def wrapper(*args, **kwargs):
        started = time.time()
        status, result = "ok", ""
        try:
            result = tool(*args, **kwargs)
            return result
        except Exception as e:
            status, result = "error", str(e)
            raise
        finally:
            try:
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tool": tool.__name__,
                        "arguments": dict(inspect.signature(tool).bind_partial(*args, **kwargs).arguments),
                        "status": status,
                        "seconds": round(time.time() - started, 3),
                        "result": str(result)[:300],
                    }) + "\n")
            except Exception:
                pass   # logging must never break a tool
    return wrapper

# ─────────────────────────────────────────
# TOPOLOGY LIFECYCLE TOOLS
# ─────────────────────────────────────────

@mcp.tool()
@logged
def create_topology(topology_type: str, hosts: int = 2,
                    switches: int = 1, aps: int = 1,
                    stations: int = 2) -> str:
    """Create and start a network topology.
    topology_type: wired, wireless, hybrid, or mesh.
    hosts/switches: used for wired. aps/stations: used for wireless."""
    global net

    if topology_type not in ["wired", "wireless", "hybrid", "mesh"]:
        raise ValueError("Invalid topology type. Use: wired, wireless, hybrid, or mesh.")
    if net is not None:
        raise ValueError("Topology already active. Call destroy_topology() first.")

    if not BACKEND_AVAILABLE:
        raise ValueError("Backend not available. Check containernet-wifi installation.")

    net = Containernet(controller=Controller)
    net.addController("c0")

    created = []

    if topology_type in ["wired", "hybrid"]:
        # Add wired switches
        switch_list = []
        for i in range(1, switches + 1):
            s = net.addSwitch(f"s{i}")
            switch_list.append(s)
            created.append(f"s{i}")

        # Add Docker hosts — distribute evenly across switches
        for i in range(1, hosts + 1):
            h = net.addDocker(
                f"h{i}",
                ip=f"10.0.0.{i}/8",
                dimage="mcp-network-node"
            )
            # Assign host to switch in round-robin order
            target_switch = switch_list[(i - 1) % len(switch_list)]
            net.addLink(h, target_switch, cls=TCLink)
            created.append(f"h{i}")

        # Chain switches if more than one
        for i in range(len(switch_list) - 1):
            net.addLink(switch_list[i], switch_list[i+1], cls=TCLink)

    if topology_type in ["wireless", "hybrid"]:
        # Add access points
        ap_list = []
        for i in range(1, aps + 1):
            ap = net.addAccessPoint(
                f"ap{i}",
                ssid=f"net-ap{i}",
                mode="g",
                channel="1",
                position=f"{50 * i},50,0"
            )
            ap_list.append(ap)
            created.append(f"ap{i}")

        # Add Docker WiFi stations
        for i in range(1, stations + 1):
            sta = net.addStation(
                f"sta{i}",
                ip=f"10.0.1.{i}/8",
                position=f"{30 * i},30,0",
                cls=DockerSta,
                dimage="mcp-network-node"
            )
            created.append(f"sta{i}")

        net.configureWifiNodes()

        for i, sta_name in enumerate([f"sta{i}" for i in range(1, stations + 1)]):
            # Distribute stations across APs in round-robin order
            target_ap = ap_list[i % len(ap_list)]
            net.addLink(net.get(sta_name), target_ap)

    if topology_type == "hybrid":
        # Connect wired switch to wireless AP
        net.addLink(switch_list[0], ap_list[0], cls=TCLink)

    if topology_type == "mesh":
        from mn_wifi.link import mesh as MeshLink
        # Add mesh stations — regular Station nodes (not DockerSta)
        # DockerSta is incompatible with mesh mode
        for i in range(1, stations + 1):
            sta = net.addStation(
                f"sta{i}",
                ip=f"10.0.2.{i}/8",
                position=f"{40 * i},50,0"
            )
            created.append(f"sta{i}")

        net.configureWifiNodes()

        # Each station joins the same mesh network independently
        for i in range(1, stations + 1):
            net.addLink(
                net.get(f"sta{i}"),
                cls=MeshLink,
                ssid="meshNet",
                intf=f"sta{i}-wlan0",
                channel=5
            )

    net.start()

    # Allow time for WiFi association to complete
    if topology_type in ["wireless", "hybrid", "mesh"]:
        import time
        time.sleep(10)

    return (
        f"Topology created ({topology_type}): "
        f"{", ".join(created)}. "
        f"Call destroy_topology() when done."
    )

@mcp.tool()
@logged
def destroy_topology() -> str:
    """Stop and clean up the active topology. Resets all backend state."""
    global net

    if net is None:
        raise ValueError("No active topology to destroy.")

    net.stop()
    net = None
    iface_state.clear()

    # Remove leftover containers created by Containernet. Containernet names its
    # containers "mn.<node name>", so this filter leaves every other Docker
    # container on the machine untouched. Each ID is passed as a separate argument.
    leftover = subprocess.run(
        ["docker", "ps", "-aq", "--filter", "name=^mn\\."],
        capture_output=True, text=True
    ).stdout.split()
    if leftover:
        subprocess.run(["docker", "rm", "-f", *leftover], capture_output=True)

    return "Topology destroyed. Backend cleaned up successfully."

# ─────────────────────────────────────────
# WIRED TOOLS (Containernet backend)
# ─────────────────────────────────────────

@mcp.tool()
@logged
def set_delay(node1: str, node2: str, delay_ms: int) -> str:
    """Apply artificial delay on the link between node1 and node2.
    delay_ms must be >= 0. Uses tc netem via TCIntf.config()."""
    require_active_topology()
    if delay_ms < 0:
        raise ValueError("delay_ms must be >= 0.")
    n1 = net.get(node1)
    n2 = net.get(node2)
    if n1 is None:
        raise ValueError(f"Node {node1} not found.")
    if n2 is None:
        raise ValueError(f"Node {node2} not found.")
    links = n1.connectionsTo(n2)
    if not links:
        raise ValueError(f"No link found between {node1} and {node2}.")

    # Apply delay to the actual link interface on node1.
    # This also handles switch-to-switch links directly.
    intf = links[0][0]
    apply_tc(intf, delay=delay_ms)
    return f"{delay_ms}ms delay set on link {node1}<->{node2} via {intf.name}."

@mcp.tool()
@logged
def set_bandwidth(node1: str, node2: str, bw_mbps: float) -> str:
    """Limit bandwidth on the link between node1 and node2.
    bw_mbps must be > 0. Uses tc via TCIntf.config()."""
    require_active_topology()
    if bw_mbps <= 0:
        raise ValueError("bw_mbps must be > 0.")
    n1 = net.get(node1)
    n2 = net.get(node2)
    if n1 is None:
        raise ValueError(f"Node {node1} not found.")
    if n2 is None:
        raise ValueError(f"Node {node2} not found.")
    links = n1.connectionsTo(n2)
    if not links:
        raise ValueError(f"No link found between {node1} and {node2}.")
    apply_tc(links[0][0], bw=bw_mbps)
    apply_tc(links[0][1], bw=bw_mbps)
    return f"{bw_mbps}Mbps bandwidth set on link {node1}<->{node2}."

@mcp.tool()
@logged
def set_loss(node1: str, node2: str, loss_pct: float) -> str:
    """Inject packet loss on the link between node1 and node2.
    loss_pct must be between 0 and 100."""
    require_active_topology()
    if loss_pct < 0 or loss_pct > 100:
        raise ValueError("loss_pct must be between 0 and 100.")
    n1 = net.get(node1)
    n2 = net.get(node2)
    if n1 is None:
        raise ValueError(f"Node {node1} not found.")
    if n2 is None:
        raise ValueError(f"Node {node2} not found.")
    links = n1.connectionsTo(n2)
    if not links:
        raise ValueError(f"No link found between {node1} and {node2}.")
    apply_tc(links[0][0], loss=loss_pct)
    apply_tc(links[0][1], loss=loss_pct)
    return f"{loss_pct}% packet loss set on link {node1}<->{node2}."

@mcp.tool()
@logged
def ping(src: str, dst: str) -> str:
    """Run a ping test from src to dst and return RTT statistics.
    Returns min/avg/max RTT in milliseconds and packet loss percentage."""
    require_active_topology()
    src_node = net.get(src)
    dst_node = net.get(dst)
    if src_node is None:
        raise ValueError(f"Node {src} not found.")
    if dst_node is None:
        raise ValueError(f"Node {dst} not found.")
    result = net.pingFull([src_node, dst_node])
    if not result:
        return f"Ping {src}->{dst}: no result returned."
    # result shape: [(src, dst, (sent, received, min, avg, max, mdev)), ...]
    stats = result[0][2]
    sent, received = stats[0], stats[1]
    rtt_min, rtt_avg, rtt_max = stats[2], stats[3], stats[4]
    loss = 0 if sent == 0 else int((sent - received) / sent * 100)
    return (
        f"Ping {src}->{dst}: "
        f"RTT min/avg/max = {rtt_min:.3f}/{rtt_avg:.3f}/{rtt_max:.3f}ms, "
        f"{loss}% packet loss."
    )

@mcp.tool()
@logged
def run_iperf(src: str, dst: str) -> str:
    """Measure TCP throughput between src and dst using iperf.
    Requires iperf and telnet installed in the container image."""
    require_active_topology()
    src_node = net.get(src)
    dst_node = net.get(dst)
    if src_node is None:
        raise ValueError(f"Node {src} not found.")
    if dst_node is None:
        raise ValueError(f"Node {dst} not found.")
    import time
    # Start iperf server on dst
    dst_node.cmd("pkill iperf 2>/dev/null; iperf -s -D")
    time.sleep(1)

    # Get dst IP address
    dst_ip = dst_node.params.get("ip", "").split("/")[0].strip()
    if not dst_ip:
        import re
        ip_out = dst_node.cmd("ip -4 addr show")
        match = re.search(r"10\.\d+\.\d+\.\d+", ip_out)
        dst_ip = match.group(0) if match else None
        if not dst_ip:
            raise ValueError(f"Could not get IP address of {dst}")

    # Run iperf client from src
    result = src_node.cmd(f"iperf -c {dst_ip} -t 5")

    # Clean up iperf server
    dst_node.cmd("pkill iperf 2>/dev/null")

    # Parse bandwidth from output
    lines = [l for l in result.splitlines() if "Gbits" in l or "Mbits" in l]
    if not lines:
        return f"Iperf {src}->{dst}: test ran but could not parse output.\n{result}"
    bandwidth = lines[-1].split()[-2] + " " + lines[-1].split()[-1]
    return f"Iperf {src}->{dst}: throughput = {bandwidth}"

# ─────────────────────────────────────────
# WIRELESS TOOLS (Mininet-WiFi backend)
# ─────────────────────────────────────────

@mcp.tool()
@logged
def set_channel(ap: str, channel: int) -> str:
    """Change the WiFi channel of an access point.
    channel must be between 1 and 13 (2.4GHz).
    Uses Mininet-WiFi native setChannel API for PHY-level channel reconfiguration."""
    require_active_topology()
    if channel < 1 or channel > 13:
        raise ValueError("channel must be between 1 and 13.")
    ap_node = net.get(ap)
    if ap_node is None:
        raise ValueError(f"AP {ap} not found.")

    # Use Mininet-WiFi native API for channel switching
    # This handles PHY-level reconfiguration correctly
    # unlike raw hostapd_cli which causes station radio PHY teardown
    ap_node.setChannel(channel)

    # Update all associated stations to the new channel
    for sta in net.stations:
        if hasattr(sta, "wintfs") and sta.wintfs:
            sta.wintfs[0].setChannel(channel)

    freq = 2407 + (channel * 5)
    return f"Channel {channel} set on {ap} (freq: {freq}MHz)."

# ─────────────────────────────────────────
# RESOURCES (read-only topology state)
# ─────────────────────────────────────────

@mcp.resource("topology://nodes")
def list_nodes() -> str:
    """List all nodes in the active topology."""
    if net is None:
        return "No active topology."
    hosts = [h.name for h in net.hosts]
    switches = [s.name for s in net.switches]
    aps = [a.name for a in net.aps] if hasattr(net, "aps") else []
    stations = [s.name for s in net.stations] if hasattr(net, "stations") else []
    return (
        f"Hosts: {hosts} | "
        f"Switches: {switches} | "
        f"APs: {aps} | "
        f"Stations: {stations}"
    )

@mcp.resource("topology://links")
def list_links() -> str:
    """List all wired links in the active topology."""
    if net is None:
        return "No active topology."
    links = []
    for link in net.links:
        try:
            n1 = link.intf1.node.name if hasattr(link.intf1, "node") else str(link.intf1)
            n2 = link.intf2.node.name if hasattr(link.intf2, "node") else str(link.intf2)
            links.append(f"{n1}<->{n2}")
        except Exception:
            pass
    return "Links: " + ", ".join(links) if links else "No links found."

@mcp.resource("topology://links/wifi")
def list_wifi_links() -> str:
    """List all wireless associations between stations and access points."""
    if net is None:
        return "No active topology."
    if not hasattr(net, "aps") or not net.aps:
        return "No wireless nodes in active topology."
    result = []
    for ap in net.aps:
        wlan = ap.params["wlan"][0]
        dump = ap.cmd(f"iw dev {wlan} station dump")
        result.append(f"AP {ap.name}: {dump.strip()}")
    return "\n".join(result)

@mcp.tool()
@logged
def get_routing_table(node: str) -> str:
    """Return the routing table of a specific node.
    Filters out Docker bridge routes (172.17.0.0/16)."""
    if net is None:
        return "No active topology."
    n = net.get(node)
    if n is None:
        raise ValueError(f"Node {node} not found.")
    output = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", n.cmd("ip route"))
    filtered = [
        line for line in output.splitlines()
        if "172.17" not in line and line.strip()
    ]
    return f"Routing table for {node}:\n" + "\n".join(filtered)

@mcp.tool()
@logged
def get_wifi_stats(ap: str) -> str:
    """Return WiFi statistics for an access point.
    Includes channel, connected stations, RSSI, and TX/RX rates."""
    if net is None:
        return "No active topology."
    ap_node = net.get(ap)
    if ap_node is None:
        raise ValueError(f"AP {ap} not found.")
    wlan = ap_node.params["wlan"][0]
    # Read channel from wintfs which reflects the current simulation state
    if hasattr(ap_node, "wintfs") and ap_node.wintfs:
        channel = ap_node.wintfs[0].channel
    else:
        channel = ap_node.params.get("channel", "unknown")
    dump = ap_node.cmd(f"iw dev {wlan} station dump")
    return f"AP {ap} | Channel: {channel}\n{dump.strip()}"

# ─────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────

@mcp.prompt()
def link_impairment_test(node1: str, node2: str,
                         host1: str, host2: str,
                         delay_ms: int = 50) -> str:
    """Reusable template for Use Case 1: link impairment and verification."""
    return (
        f"First ping from {host1} to {host2} as a baseline. "
        f"Then add {delay_ms}ms delay on the link between {node1} and {node2}, "
        f"ping again and compare both round-trip times."
    )

@mcp.prompt()
def wifi_channel_test(ap: str, rssi_threshold: int = -70) -> str:
    """Reusable template for Use Case 2: WiFi channel optimisation."""
    return (
        f"Check signal quality of all stations on {ap}. "
        f"If any RSSI is below {rssi_threshold}dBm, "
        f"switch {ap} to channel 11 and re-check."
    )

if __name__ == "__main__":
    mcp.run()
