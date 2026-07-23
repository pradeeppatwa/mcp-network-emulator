from mcp.server.fastmcp import FastMCP

# Global state — single unified backend (ramonfontes/containernet)
# Handles Docker hosts, Docker WiFi stations, wired switches, and APs
net = None  # live Containernet net object

def require_active_topology():
    """Guard function — every tool calls this first."""
    if net is None:
        raise ValueError("No active topology. Call create_topology() first.")

mcp = FastMCP("network-emulator")

# ─────────────────────────────────────────
# TOPOLOGY LIFECYCLE TOOLS
# ─────────────────────────────────────────

@mcp.tool()
def create_topology(topology_type: str, hosts: int = 2,
                    switches: int = 1, aps: int = 1,
                    stations: int = 2) -> str:
    """Create and start a network topology.
    topology_type: wired, wireless, or hybrid.
    hosts/switches: used for wired. aps/stations: used for wireless."""
    if topology_type not in ["wired", "wireless", "hybrid"]:
        raise ValueError("Invalid topology type. Use: wired, wireless, or hybrid.")
    if net is not None:
        raise ValueError("Topology already active. Call destroy_topology() first.")
    return f"[MOCK] Would create {topology_type} topology: {hosts} hosts, {switches} switches, {aps} APs, {stations} stations."

@mcp.tool()
def destroy_topology() -> str:
    """Stop and clean up the active topology. Resets all backend state."""
    if net is None:
        raise ValueError("No active topology to destroy.")
    return "[MOCK] Would destroy active topology and clean up backend."

# ─────────────────────────────────────────
# WIRED TOOLS (Containernet backend)
# ─────────────────────────────────────────

@mcp.tool()
def set_delay(node1: str, node2: str, delay_ms: int) -> str:
    """Apply artificial delay on the link between node1 and node2.
    delay_ms must be >= 0. Uses tc netem via TCIntf.config()."""
    require_active_topology()
    if delay_ms < 0:
        raise ValueError("delay_ms must be >= 0.")
    return f"[MOCK] Would set {delay_ms}ms delay on link {node1}<->{node2}."

@mcp.tool()
def set_bandwidth(node1: str, node2: str, bw_mbps: float) -> str:
    """Limit bandwidth on the link between node1 and node2.
    bw_mbps must be > 0. Uses tc via TCIntf.config()."""
    require_active_topology()
    if bw_mbps <= 0:
        raise ValueError("bw_mbps must be > 0.")
    return f"[MOCK] Would set {bw_mbps}Mbps bandwidth on link {node1}<->{node2}."

@mcp.tool()
def set_loss(node1: str, node2: str, loss_pct: float) -> str:
    """Inject packet loss on the link between node1 and node2.
    loss_pct must be between 0 and 100."""
    require_active_topology()
    if loss_pct < 0 or loss_pct > 100:
        raise ValueError("loss_pct must be between 0 and 100.")
    return f"[MOCK] Would set {loss_pct}% packet loss on link {node1}<->{node2}."

@mcp.tool()
def ping(src: str, dst: str) -> str:
    """Run a ping test from src to dst and return RTT statistics.
    Returns min/avg/max RTT in milliseconds and packet loss percentage."""
    require_active_topology()
    return f"[MOCK] Would ping {src}->{dst} and return RTT stats."

@mcp.tool()
def run_iperf(src: str, dst: str) -> str:
    """Measure TCP throughput between src and dst using iperf.
    Requires iperf and telnet installed in the container image."""
    require_active_topology()
    return f"[MOCK] Would run iperf {src}->{dst} and return throughput."

# ─────────────────────────────────────────
# WIRELESS TOOLS (Mininet-WiFi backend)
# ─────────────────────────────────────────

@mcp.tool()
def set_channel(ap: str, channel: int) -> str:
    """Change the WiFi channel of an access point.
    channel must be between 1 and 13 (2.4GHz).
    Uses hostapd_cli chan_switch internally."""
    require_active_topology()
    if channel < 1 or channel > 13:
        raise ValueError("channel must be between 1 and 13.")
    freq = 2407 + (channel * 5)
    return f"[MOCK] Would switch {ap} to channel {channel} (freq: {freq}MHz)."

# ─────────────────────────────────────────
# RESOURCES (read-only topology state)
# ─────────────────────────────────────────

@mcp.resource("topology://nodes")
def list_nodes() -> str:
    """List all nodes in the active topology.
    Returns hosts, switches, access points, and stations."""
    if net is None:
        return "No active topology."
    return "[MOCK] Would return: Hosts: [h1,h2] Switches: [s1] APs: [ap1] Stations: [sta1,sta2]"

@mcp.resource("topology://links")
def list_links() -> str:
    """List all wired links with current TC settings (delay, bandwidth, loss)."""
    if net is None:
        return "No active topology."
    return "[MOCK] Would return: h1<->s1: delay=0ms bw=unlimited loss=0%"

@mcp.resource("topology://links/wifi")
def list_wifi_links() -> str:
    """List all wireless associations between stations and access points."""
    if net is None:
        return "No active topology."
    return "[MOCK] Would return: sta1->ap1: signal=-36dBm channel=5"

@mcp.tool()
def get_routing_table(node: str) -> str:
    """Return the routing table of a specific node.
    Filters out Docker bridge routes (172.17.0.0/16)."""
    if net is None:
        return "No active topology."
    return f"[MOCK] Would return ip route output for {node}, filtered."

@mcp.tool()
def get_wifi_stats(ap: str) -> str:
    """Return WiFi statistics for an access point.
    Includes channel, connected stations, RSSI, and TX/RX rates.
    Uses iw dev station dump internally."""
    if net is None:
        return "No active topology."
    return f"[MOCK] Would return iw station dump for {ap}."

# ─────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────

@mcp.prompt()
def link_impairment_test(node1: str, node2: str,
                         host1: str, host2: str,
                         delay_ms: int = 50) -> str:
    """Reusable template for Use Case 1: link impairment and verification."""
    return (
        f"Add {delay_ms}ms delay on the link between {node1} and {node2}, "
        f"then ping from {host1} to {host2} and confirm the RTT increased."
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
