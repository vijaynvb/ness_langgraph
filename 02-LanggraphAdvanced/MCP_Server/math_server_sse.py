from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP(name="Ness_Math_MCP_Server", host="127.0.0.1", port=8000)


@mcp_server.tool(name="add")
def add(a: float, b: float) -> float:
    """Add two numbers and return the result """
    return a * b

if __name__ == "__main__":
    print("MCP server running at http://127.0.0.1:8000/sse")
    mcp_server.run(transport="sse")
