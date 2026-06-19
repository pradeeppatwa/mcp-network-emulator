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

if __name__ == "__main__":
    mcp.run()
