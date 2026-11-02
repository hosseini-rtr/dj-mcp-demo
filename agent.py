
import asyncio
import json
import os

from ollama import AsyncClient
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_URL = os.getenv(
    "MCP_URL",
    "http://localhost:8001/mcp",
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
)

MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")


async def main():
    ollama = AsyncClient(host=OLLAMA_URL)

    async with streamable_http_client(MCP_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as mcp:

            await mcp.initialize()

            # Discover MCP tools
            available = await mcp.list_tools()

            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in available.tools
            ]

            print("Available tools:", [
                tool["function"]["name"] for tool in tools
            ])

            messages = [
                {
                    "role": "user",
                    "content": "Find customer with ID 1 and tell me their details.",
                }
            ]

            # Agent loop
            while True:
                response = await ollama.chat(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                )

                messages.append(response.message)

                tool_calls = response.message.tool_calls

                if not tool_calls:
                    print("\nAssistant:")
                    print(response.message.content)
                    break

                for call in tool_calls:
                    name = call.function.name
                    arguments = call.function.arguments

                    print(f"\nCalling MCP tool: {name}")
                    print("Arguments:", arguments)

                    result = await mcp.call_tool(
                        name,
                        arguments,
                    )

                    content = "\n".join(
                        item.text
                        for item in result.content
                        if hasattr(item, "text")
                    )

                    messages.append({
                        "role": "tool",
                        "tool_name": name,
                        "content": content,
                    })


if __name__ == "__main__":
    asyncio.run(main())
