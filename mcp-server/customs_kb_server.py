#!/usr/bin/env python3
"""
MCP Server for US Customs Knowledge Base
Provides tools for searching Federal Register documents and HTS codes
"""
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# API base URL
API_BASE = "http://localhost:8000"

# Initialize MCP server
app = Server("customs-kb")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_customs_documents",
            description="Search US Federal Register documents for customs and trade regulations. Returns relevant CBP rulings, notices, and rules from 1994-present.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'steel antidumping duties', 'textile import quotas')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (1-50)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "hts_code": {
                        "type": "string",
                        "description": "Optional HTS code filter (e.g., '8703' for motor vehicles)",
                        "default": None
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_hts_codes",
            description="Search Harmonized Tariff Schedule (HTS) codes by product description. Returns tariff codes with duty rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product description to search (e.g., 'cheese', 'automobiles', 'electronics')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_hts_code_details",
            description="Get detailed information about a specific HTS tariff code including duty rates and special rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hts_number": {
                        "type": "string",
                        "description": "HTS code number (e.g., '0406.10.00' for fresh cheese)"
                    }
                },
                "required": ["hts_number"]
            }
        ),
        Tool(
            name="get_customs_kb_status",
            description="Get statistics about the customs knowledge base including document counts and recent updates.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    async with httpx.AsyncClient() as client:
        try:
            if name == "search_customs_documents":
                query = arguments["query"]
                limit = arguments.get("limit", 5)
                hts_code = arguments.get("hts_code")

                # Build URL
                url = f"{API_BASE}/api/search?q={query}&limit={limit}"
                if hts_code:
                    url += f"&hts_code={hts_code}"

                response = await client.get(url)
                response.raise_for_status()
                results = response.json()

                if not results:
                    return [TextContent(
                        type="text",
                        text="No documents found matching your query."
                    )]

                # Format results
                output = f"Found {len(results)} relevant customs documents:\n\n"
                for i, doc in enumerate(results, 1):
                    output += f"{i}. **{doc['title']}**\n"
                    output += f"   - Document Number: {doc['document_number']}\n"
                    output += f"   - Type: {doc.get('type', 'N/A')}\n"
                    output += f"   - Date: {doc.get('date', 'N/A')}\n"
                    output += f"   - Relevance Score: {doc['score']:.3f}\n"
                    if doc.get('excerpt'):
                        output += f"   - Excerpt: {doc['excerpt']}\n"
                    if doc.get('url'):
                        output += f"   - URL: {doc['url']}\n"
                    output += "\n"

                return [TextContent(type="text", text=output)]

            elif name == "search_hts_codes":
                query = arguments["query"]
                limit = arguments.get("limit", 10)

                response = await client.get(
                    f"{API_BASE}/api/hts/search?q={query}&limit={limit}"
                )
                response.raise_for_status()
                results = response.json()

                if not results:
                    return [TextContent(
                        type="text",
                        text="No HTS codes found matching your query."
                    )]

                # Format results
                output = f"Found {len(results)} HTS tariff codes:\n\n"
                for i, code in enumerate(results, 1):
                    output += f"{i}. **HTS {code['hts_number']}**: {code['description']}\n"
                    if code.get('general_rate'):
                        output += f"   - General Duty Rate: {code['general_rate']}\n"
                    if code.get('special_rate'):
                        output += f"   - Special Duty Rate: {code['special_rate']}\n"
                    output += "\n"

                return [TextContent(type="text", text=output)]

            elif name == "get_hts_code_details":
                hts_number = arguments["hts_number"]

                response = await client.get(f"{API_BASE}/api/hts/{hts_number}")
                response.raise_for_status()
                code = response.json()

                # Format detailed info
                output = f"**HTS Code: {code['hts_number']}**\n\n"
                output += f"Description: {code['description']}\n\n"
                if code.get('general_rate'):
                    output += f"General Duty Rate: {code['general_rate']}\n"
                if code.get('special_rate'):
                    output += f"Special Duty Rate: {code['special_rate']}\n"
                if code.get('indent_level') is not None:
                    output += f"Indent Level: {code['indent_level']}\n"
                if code.get('parent_hts_number'):
                    output += f"Parent Code: {code['parent_hts_number']}\n"

                return [TextContent(type="text", text=output)]

            elif name == "get_customs_kb_status":
                response = await client.get(f"{API_BASE}/api/status")
                response.raise_for_status()
                status = response.json()

                output = "**US Customs Knowledge Base Status**\n\n"
                output += f"- Federal Register Documents: {status['documents_count']:,}\n"
                output += f"- HTS Tariff Codes: {status['hts_codes_count']:,}\n"
                output += f"- Vector Embeddings: {status['vector_points']:,}\n\n"
                output += "Recent Ingestions:\n"
                for ing in status['recent_ingestions'][:3]:
                    output += f"  - {ing['source']}: {ing['documents']} items ({ing['status']})\n"

                return [TextContent(type="text", text=output)]

            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=f"Error calling Customs KB API: {str(e)}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
