from mcp.server.fastmcp import FastMCP

mcp = FastMCP("network-emulator")

@mcp.tool()
def ping_test() -> str:
    """Sanity check tool confirming the MCP server process is alive."""
    return "MCP server operational. Containernet/Mininet-WiFi backend not yet wired."

@mcp.tool()
def set_delay_mock(node1: str, node2: str, delay_ms: int) -> str:
    """Mock version of the future set_delay tool — returns a formatted
    confirmation without touching Containernet yet."""
    return f"[MOCK] Would set {delay_ms}ms delay on link {node1}<->{node2}"

@mcp.resource("topology://demo")
def demo_topology() -> str:
    """Static placeholder describing a fake topology — real topology
    data wires in once Containernet/Mininet-WiFi integration starts (Phase 3)."""
    return "h1 -- s1 -- s2 -- h2 (placeholder, no real backend wired yet)"

if __name__ == "__main__":
    mcp.run()
