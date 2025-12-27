"""
MCP Server for CatalogAI with code execution capability.
"""
from mcp.server.fastmcp import FastMCP
from code_executor import CodeExecutor

mcp = FastMCP("catalogai-code-execution")
executor = CodeExecutor()


@mcp.tool()
async def execute_code(code: str, user_context: dict) -> dict:
    """
    Execute Python code with catalogai SDK.

    This allows Claude to write Python code that interacts with your catalog system,
    process data locally, and return compact results.

    Args:
        code: Python code to execute (has access to catalogai SDK)
        user_context: User auth token and org info

    Returns:
        Execution result with output

    Example:
        ```python
        import catalogai

        client = catalogai.CatalogAIClient(
            base_url=os.getenv("CATALOGAI_API_URL"),
            auth_token=os.getenv("CATALOGAI_AUTH_TOKEN")
        )

        # Search for laptops
        results = client.catalog.search(query="laptop", limit=5)
        print(f"Found {len(results)} laptops")
        ```
    """
    result = executor.execute(code, {
        "api_url": user_context.get("api_url", "http://localhost:5000"),
        "auth_token": user_context["auth_token"]
    })
    return result


@mcp.tool()
async def search_catalog(query: str, threshold: float = 0.3, limit: int = 10) -> list:
    """
    Search catalog items using semantic similarity.

    This is a simple wrapper tool for quick searches without code execution.

    Args:
        query: Natural language search query
        threshold: Minimum similarity score (0-1)
        limit: Maximum number of results

    Returns:
        List of matching catalog items with similarity scores
    """
    # This would use a direct API call
    # For now, we'll note that this should be implemented
    return {"error": "Use execute_code for catalog operations"}


def main():
    """Run MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
