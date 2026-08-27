
from mcp.server.fastmcp import FastMCP 

mcp_server = FastMCP(name="Ness_Math_MCP_Server")


@mcp_server.tool(name="add")
def add(a: float, b: float) -> float:
    """Add two numbers and return the result """
    return a * b

if __name__ == "__main__":
    mcp_server.run(transport="stdio")
