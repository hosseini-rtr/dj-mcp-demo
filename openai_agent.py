
import asyncio
import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8001/mcp")
MODEL = os.environ["LLM_MODEL"]

client = AsyncOpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    default_headers={
        "x-user-id": os.getenv("LLM_USER_ID", "demo-user"),
        "x-request-id": os.getenv("LLM_REQUEST_ID", "dj-mcp-demo"),
        "x-session-id": os.getenv("LLM_SESSION_ID", "Session999"),
    },
)


def convert_mcp_tools(tools):
    """Convert MCP tool definitions to OpenAI function tools."""

    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


def serialize_tool_result(result):
    """Convert MCP tool result to text for the LLM."""

    contents = []

    for item in result.content:
        if hasattr(item, "text"):
            contents.append(item.text)

    if contents:
        return "\n".join(contents)

    return json.dumps(
        {"error": "Tool returned no text content."},
        ensure_ascii=False,
    )


async def run_agent(prompt: str):
    async with streamable_http_client(MCP_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(read_stream, write_stream) as mcp:
            await mcp.initialize()

            # Discover available MCP tools.
            mcp_tools = await mcp.list_tools()
            tools = convert_mcp_tools(mcp_tools.tools)

            print(f"Discovered {len(tools)} MCP tools:")
            for tool in tools:
                print(f"- {tool['function']['name']}")

            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]

            # Prevent an endless tool-calling loop.
            max_iterations = 8

            for _ in range(max_iterations):
                response = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )

                assistant_message = response.choices[0].message

                # Preserve the assistant message, including tool_calls.
                messages.append(
                    assistant_message.model_dump(exclude_none=True)
                )

                # No more tools: return the final answer.
                if not assistant_message.tool_calls:
                    return assistant_message.content or ""

                # Execute requested MCP tools.
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name

                    try:
                        arguments = json.loads(
                            tool_call.function.arguments or "{}"
                        )

                        if not isinstance(arguments, dict):
                            raise ValueError(
                                "Tool arguments must be a JSON object."
                            )

                        print(f"\nExecuting MCP tool: {tool_name}")
                        print(f"Arguments: {arguments}")

                        result = await mcp.call_tool(
                            tool_name,
                            arguments,
                        )

                        tool_output = serialize_tool_result(result)

                        if result.isError:
                            tool_output = json.dumps(
                                {"error": tool_output},
                                ensure_ascii=False,
                            )

                    except Exception as exc:
                        tool_output = json.dumps(
                            {"error": str(exc)},
                            ensure_ascii=False,
                        )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_output,
                        }
                    )

            raise RuntimeError(
                f"Maximum tool-call iterations ({max_iterations}) reached."
            )


async def main():
    prompt = input("You: ").strip()

    if not prompt:
        return

    try:
        answer = await run_agent(prompt)
        print(f"\nAssistant: {answer}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
