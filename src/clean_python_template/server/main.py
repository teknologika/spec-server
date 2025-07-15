from fastmcp import FastMCP
from clean_python_template.core.math import add

mcp = FastMCP("CleanPythonTemplate")


@mcp.tool()
def add_tool(a: int, b: int) -> int:
    """Add two numbers."""
    return add(a, b)


if __name__ == "__main__":
    mcp.run()
