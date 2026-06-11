""" MCP Client Test Script
===============================
Connects to mcp_server.py over stdio, lists tools/resources,
and calls each tool to confirm discovery works.
"""

import asyncio
import json

from fastmcp import Client


async def main():
    # Connect to the MCP server over stdio
    client = Client("mcp_server.py")

    async with client:
        # ── 1. List all tools ──
        print("=" * 50)
        print("DISCOVERED TOOLS")
        print("=" * 50)
        tools = await client.list_tools()
        for tool in tools:
            print(f"  🔧 {tool.name}: {tool.description}")

        # ── 2. List all resources ──
        print("\n" + "=" * 50)
        print("DISCOVERED RESOURCES")
        print("=" * 50)
        resources = await client.list_resource_templates()
        for resource in resources:
            print(f"  📦 {resource.uriTemplate}: {resource.description}")

        # ── 3. Call get_shipment_status ──
        print("\n" + "=" * 50)
        print("CALLING: get_shipment_status(id=1)")
        print("=" * 50)
        try:
            result = await client.call_tool(
                "get_shipment_status", {"id": 1}
            )
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")

        # ── 4. Call list_delayed_shipments ──
        print("\n" + "=" * 50)
        print("CALLING: list_delayed_shipments()")
        print("=" * 50)
        try:
            result = await client.call_tool(
                "list_delayed_shipments", {}
            )
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")

        # ── 5. Read resource ──
        print("\n" + "=" * 50)
        print("READING RESOURCE: shipment://1")
        print("=" * 50)
        try:
            result = await client.read_resource("shipment://1")
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n✅ All MCP discovery checks complete!")


if __name__ == "__main__":
    asyncio.run(main())