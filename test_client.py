
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    async with streamable_http_client(
        "http://localhost:8001/mcp"
    ) as (read_stream, write_stream):

        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()

            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # Test ping
            ping_result = await session.call_tool("ping", {})
            print("\nPing result:")
            print(ping_result)

            # Test get_customer
            customer_result = await session.call_tool(
                "get_customer",
                {"customer_id": 1},
            )

            print("\nCustomer result:")
            print(customer_result)


if __name__ == "__main__":
    asyncio.run(main())
