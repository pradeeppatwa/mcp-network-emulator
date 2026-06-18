from mcp.server.fastmcp import FastMCP

mcp = FastMCP("network-emulator")

@mcp.tool()
def ping_test() -> str:
    """Sanity check tool confirming the MCP server process is alive."""
    return "MCP server operational. Containernet/Mininet-WiFi backend not yet wired."

if __name__ == "__main__":
    mcp.run()
