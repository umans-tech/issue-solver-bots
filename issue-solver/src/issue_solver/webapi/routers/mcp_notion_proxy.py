"""Notion MCP Proxy Router - REST-backed MCP tools for Notion."""

import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from issue_solver.clock import Clock
from issue_solver.events.event_store import EventStore
from issue_solver.events.notion_integration import get_notion_credentials
from issue_solver.webapi.dependencies import get_clock, get_event_store, get_logger
from issue_solver.webapi.routers.notion_integration import (
    ensure_fresh_notion_credentials,
)

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

router = APIRouter()


# MCP Tool Definitions
NOTION_TOOLS = [
    {
        "name": "notion_search",
        "description": "Search across all pages and databases in the Notion workspace. Returns titles, IDs, and basic metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The text to search for",
                },
                "filter": {
                    "type": "object",
                    "description": "Optional filter by object type (page or database)",
                    "properties": {
                        "value": {
                            "type": "string",
                            "enum": ["page", "database"],
                        },
                        "property": {
                            "type": "string",
                            "enum": ["object"],
                        },
                    },
                },
                "sort": {
                    "type": "object",
                    "description": "Sort results by last edited time",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["ascending", "descending"],
                        },
                        "timestamp": {
                            "type": "string",
                            "enum": ["last_edited_time"],
                        },
                    },
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "notion_get_page",
        "description": "Retrieve a Notion page by its ID. Returns page properties and metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page to retrieve",
                }
            },
            "required": ["page_id"],
        },
    },
    {
        "name": "notion_get_block_children",
        "description": "Get the content blocks of a page or block. Returns the actual content of a Notion page.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "The ID of the block or page to get children from",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of blocks to return (max 100)",
                    "default": 100,
                },
            },
            "required": ["block_id"],
        },
    },
    {
        "name": "notion_list_databases",
        "description": "List all databases in the Notion workspace. Returns database titles, IDs, and metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "notion_get_database",
        "description": "Get database schema and properties. Shows what fields/columns a database has before querying it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database_id": {
                    "type": "string",
                    "description": "The ID of the database",
                },
            },
            "required": ["database_id"],
        },
    },
    {
        "name": "notion_query_database",
        "description": "Query a database with optional filters and sorts. Returns matching database entries with their properties.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database_id": {
                    "type": "string",
                    "description": "The ID of the database to query",
                },
                "filter": {
                    "type": "object",
                    "description": "Optional Notion filter object to filter results",
                },
                "sorts": {
                    "type": "array",
                    "description": "Optional array of sort objects",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of results to return (max 100)",
                    "default": 100,
                },
            },
            "required": ["database_id"],
        },
    },
    {
        "name": "notion_create_page",
        "description": "Create a new page in a database. Properties must be in Notion API format. IMPORTANT: Use notion_get_database first to see property types, then format accordingly. Title properties need {title: [{text: {content: 'value'}}]}, select needs {select: {name: 'value'}}.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent": {
                    "type": "object",
                    "description": "Parent reference: {database_id: 'xxx'} or {page_id: 'xxx'}",
                },
                "properties": {
                    "type": "object",
                    "description": "Properties in Notion API format. Example: {'Name': {'title': [{'text': {'content': 'Task'}}]}, 'Status': {'select': {'name': 'Todo'}}}",
                },
                "children": {
                    "type": "array",
                    "description": "Optional content blocks",
                },
            },
            "required": ["parent", "properties"],
        },
    },
    {
        "name": "notion_update_page",
        "description": "Update properties of an existing page. Properties must be in Notion API format (same as notion_create_page).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page to update",
                },
                "properties": {
                    "type": "object",
                    "description": "Properties in Notion API format. Example: {'Status': {'select': {'name': 'Done'}}}",
                },
                "archived": {
                    "type": "boolean",
                    "description": "Optional: Set to true to archive the page",
                },
            },
            "required": ["page_id", "properties"],
        },
    },
    {
        "name": "notion_append_blocks",
        "description": "Append content blocks to a page or block. Supports paragraph, heading, list, and checkbox blocks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "The ID of the page or block to append to",
                },
                "children": {
                    "type": "array",
                    "description": "Array of block objects to append",
                },
            },
            "required": ["block_id", "children"],
        },
    },
]


@router.post("/mcp/notion/proxy")
async def proxy_notion_mcp(
    raw_request: Request,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion_mcp")),
    ],
) -> JSONResponse:
    """Handle MCP JSON-RPC requests for Notion tools."""
    try:
        payload: dict[str, Any] = await raw_request.json()
        method = payload.get("method")
        request_id = payload.get("id")

        # Extract user context
        user_id = payload.get("meta", {}).get("user_id")
        space_id = payload.get("meta", {}).get("space_id")

        if not space_id:
            return _error_response(
                request_id,
                -32602,
                "Missing space_id in request metadata",
            )

        # Get and refresh credentials
        credentials = await get_notion_credentials(event_store, space_id)
        if not credentials:
            return _error_response(
                request_id,
                -32001,
                "No Notion integration connected to this space",
            )

        credentials = await ensure_fresh_notion_credentials(
            event_store=event_store,
            credentials=credentials,
            space_id=space_id,
            user_id=user_id or "unknown-user-id",
            clock=clock,
            logger=logger,
        )

        logger.info(
            "Processing Notion MCP request: method=%s, space=%s",
            method,
            space_id,
        )

        # Handle MCP protocol methods
        if method == "initialize":
            return _success_response(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": "notion-mcp-proxy",
                        "version": "1.0.0",
                    },
                },
            )

        if method == "tools/list":
            return _success_response(request_id, {"tools": NOTION_TOOLS})

        if method == "tools/call":
            tool_name = payload.get("params", {}).get("name")
            tool_args = payload.get("params", {}).get("arguments", {})

            result = await _call_notion_tool(
                tool_name=tool_name,
                arguments=tool_args,
                access_token=credentials.access_token,
                logger=logger,
            )
            return _success_response(request_id, result)

        return _error_response(
            request_id,
            -32601,
            f"Unknown method: {method}",
        )

    except HTTPException as exc:
        logger.warning("HTTP exception in Notion MCP proxy: %s", exc.detail)
        return _error_response(
            request_id if "request_id" in locals() else None,
            exc.status_code,
            str(exc.detail),
        )
    except Exception:
        logger.exception("Unexpected error in Notion MCP proxy")
        return _error_response(
            request_id if "request_id" in locals() else None,
            -32603,
            "Internal server error",
        )


async def _call_notion_tool(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Execute a Notion tool by calling the REST API."""
    if tool_name == "notion_search":
        return await _notion_search(arguments, access_token, logger)
    elif tool_name == "notion_get_page":
        return await _notion_get_page(arguments, access_token, logger)
    elif tool_name == "notion_get_block_children":
        return await _notion_get_block_children(arguments, access_token, logger)
    elif tool_name == "notion_list_databases":
        return await _notion_list_databases(arguments, access_token, logger)
    elif tool_name == "notion_get_database":
        return await _notion_get_database(arguments, access_token, logger)
    elif tool_name == "notion_query_database":
        return await _notion_query_database(arguments, access_token, logger)
    elif tool_name == "notion_create_page":
        return await _notion_create_page(arguments, access_token, logger)
    elif tool_name == "notion_update_page":
        return await _notion_update_page(arguments, access_token, logger)
    elif tool_name == "notion_append_blocks":
        return await _notion_append_blocks(arguments, access_token, logger)
    else:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")


async def _notion_search(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Search Notion workspace using the search API."""
    query = arguments.get("query", "")
    filter_obj = arguments.get("filter")
    sort_obj = arguments.get("sort")

    payload: dict[str, Any] = {"query": query}
    if filter_obj:
        payload["filter"] = filter_obj
    if sort_obj:
        payload["sort"] = sort_obj

    data = await _notion_api_request(
        "POST",
        "/search",
        access_token,
        logger,
        json_payload=payload,
    )

    # Format results for MCP response
    results = data.get("results", [])
    formatted_results = []
    for item in results:
        formatted_item = {
            "id": item.get("id"),
            "object": item.get("object"),
            "created_time": item.get("created_time"),
            "last_edited_time": item.get("last_edited_time"),
            "url": item.get("url"),
        }

        # Extract title based on object type
        if item.get("object") == "page":
            properties = item.get("properties", {})
            title_prop = properties.get("title", {})
            if title_prop:
                title_content = title_prop.get("title", [])
                if title_content:
                    formatted_item["title"] = title_content[0].get("plain_text", "")
        elif item.get("object") == "database":
            title_list = item.get("title", [])
            if title_list:
                formatted_item["title"] = title_list[0].get("plain_text", "")

        formatted_results.append(formatted_item)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Found {len(formatted_results)} results",
            }
        ],
        "isError": False,
        "_meta": {
            "results": formatted_results,
            "has_more": data.get("has_more", False),
        },
    }


async def _notion_get_page(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Get a Notion page by ID."""
    page_id = arguments.get("page_id")
    if not page_id:
        raise HTTPException(status_code=400, detail="page_id is required")

    data = await _notion_api_request(
        "GET",
        f"/pages/{page_id}",
        access_token,
        logger,
    )

    return {
        "content": [
            {
                "type": "text",
                "text": f"Retrieved page: {page_id}",
            }
        ],
        "isError": False,
        "_meta": data,
    }


async def _notion_get_block_children(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Get block children (content) from a page or block."""
    block_id = arguments.get("block_id")
    if not block_id:
        raise HTTPException(status_code=400, detail="block_id is required")

    page_size = arguments.get("page_size", 100)

    data = await _notion_api_request(
        "GET",
        f"/blocks/{block_id}/children?page_size={page_size}",
        access_token,
        logger,
    )

    # Extract text content from blocks
    blocks = data.get("results", [])
    content_parts = []

    for block in blocks:
        block_type = block.get("type")
        block_content = block.get(block_type, {})

        # Extract text from rich_text fields
        if "rich_text" in block_content:
            for text_obj in block_content["rich_text"]:
                if text_obj.get("plain_text"):
                    content_parts.append(text_obj["plain_text"])

    content_text = (
        "\n".join(content_parts) if content_parts else "No text content found"
    )

    return {
        "content": [
            {
                "type": "text",
                "text": content_text,
            }
        ],
        "isError": False,
        "_meta": {
            "block_count": len(blocks),
            "has_more": data.get("has_more", False),
            "blocks": blocks,
        },
    }


async def _notion_list_databases(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """List all databases in the Notion workspace."""
    # Search for databases only
    payload = {
        "filter": {"property": "object", "value": "database"},
        "page_size": 100,
    }

    data = await _notion_api_request(
        "POST",
        "/search",
        access_token,
        logger,
        json_payload=payload,
    )

    # Format database list
    results = data.get("results", [])
    formatted_databases = []
    for db in results:
        formatted_db = {
            "id": db.get("id"),
            "title": "",
            "url": db.get("url"),
            "created_time": db.get("created_time"),
            "last_edited_time": db.get("last_edited_time"),
        }

        # Extract title
        title_list = db.get("title", [])
        if title_list:
            formatted_db["title"] = title_list[0].get("plain_text", "Untitled")

        formatted_databases.append(formatted_db)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Found {len(formatted_databases)} databases",
            }
        ],
        "isError": False,
        "_meta": {
            "databases": formatted_databases,
            "has_more": data.get("has_more", False),
        },
    }


async def _notion_get_database(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Get database schema and properties."""
    database_id = arguments.get("database_id")
    if not database_id:
        raise HTTPException(status_code=400, detail="database_id is required")

    data = await _notion_api_request(
        "GET",
        f"/databases/{database_id}",
        access_token,
        logger,
    )

    # Extract database schema information
    title = ""
    title_list = data.get("title", [])
    if title_list:
        title = title_list[0].get("plain_text", "Untitled")

    properties = data.get("properties", {})
    property_schema = {}
    for prop_name, prop_config in properties.items():
        property_schema[prop_name] = {
            "type": prop_config.get("type"),
            "id": prop_config.get("id"),
        }

    return {
        "content": [
            {
                "type": "text",
                "text": f"Database: {title}\nProperties: {len(property_schema)}",
            }
        ],
        "isError": False,
        "_meta": {
            "id": data.get("id"),
            "title": title,
            "url": data.get("url"),
            "properties": property_schema,
            "created_time": data.get("created_time"),
            "last_edited_time": data.get("last_edited_time"),
        },
    }


async def _notion_query_database(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Query a database with optional filters and sorts."""
    database_id = arguments.get("database_id")
    if not database_id:
        raise HTTPException(status_code=400, detail="database_id is required")

    # Build query payload
    payload: dict[str, Any] = {}
    if arguments.get("filter"):
        payload["filter"] = arguments["filter"]
    if arguments.get("sorts"):
        payload["sorts"] = arguments["sorts"]

    page_size = arguments.get("page_size", 100)
    payload["page_size"] = min(page_size, 100)

    data = await _notion_api_request(
        "POST",
        f"/databases/{database_id}/query",
        access_token,
        logger,
        json_payload=payload,
    )

    # Format query results
    results = data.get("results", [])
    formatted_results = []
    for page in results:
        formatted_page = {
            "id": page.get("id"),
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "properties": {},
        }

        # Extract property values
        properties = page.get("properties", {})
        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get("type")
            formatted_page["properties"][prop_name] = {
                "type": prop_type,
            }

            # Extract value based on type
            if prop_type == "title":
                title_content = prop_value.get("title", [])
                if title_content:
                    formatted_page["properties"][prop_name]["value"] = title_content[
                        0
                    ].get("plain_text", "")
            elif prop_type == "rich_text":
                rich_text = prop_value.get("rich_text", [])
                if rich_text:
                    formatted_page["properties"][prop_name]["value"] = rich_text[0].get(
                        "plain_text", ""
                    )
            elif prop_type in ["number", "checkbox", "url", "email", "phone_number"]:
                formatted_page["properties"][prop_name]["value"] = prop_value.get(
                    prop_type
                )
            elif prop_type == "select":
                select_obj = prop_value.get("select")
                if select_obj:
                    formatted_page["properties"][prop_name]["value"] = select_obj.get(
                        "name"
                    )
            elif prop_type == "multi_select":
                multi_select = prop_value.get("multi_select", [])
                formatted_page["properties"][prop_name]["value"] = [
                    item.get("name") for item in multi_select
                ]
            elif prop_type == "status":
                status_obj = prop_value.get("status")
                if status_obj:
                    formatted_page["properties"][prop_name]["value"] = status_obj.get(
                        "name"
                    )
            elif prop_type == "date":
                date_obj = prop_value.get("date")
                if date_obj:
                    formatted_page["properties"][prop_name]["value"] = date_obj.get(
                        "start"
                    )

        formatted_results.append(formatted_page)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Found {len(formatted_results)} entries",
            }
        ],
        "isError": False,
        "_meta": {
            "results": formatted_results,
            "has_more": data.get("has_more", False),
        },
    }


async def _notion_create_page(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Create a new page in a database or as a child of another page."""
    parent = arguments.get("parent")
    properties = arguments.get("properties")

    if not parent:
        raise HTTPException(status_code=400, detail="parent is required")
    if not properties:
        raise HTTPException(status_code=400, detail="properties is required")

    # Build the request payload
    payload: dict[str, Any] = {
        "parent": parent,
        "properties": _format_properties_for_api(properties),
    }

    # Add children blocks if provided
    if arguments.get("children"):
        payload["children"] = arguments["children"]

    data = await _notion_api_request(
        "POST",
        "/pages",
        access_token,
        logger,
        json_payload=payload,
    )

    # Extract page title
    page_title = "Untitled"
    page_properties = data.get("properties", {})
    for prop_value in page_properties.values():
        if prop_value.get("type") == "title":
            title_content = prop_value.get("title", [])
            if title_content:
                page_title = title_content[0].get("plain_text", "Untitled")
                break

    return {
        "content": [
            {
                "type": "text",
                "text": f"Created page: {page_title}",
            }
        ],
        "isError": False,
        "_meta": {
            "page_id": data.get("id"),
            "url": data.get("url"),
            "created_time": data.get("created_time"),
        },
    }


async def _notion_update_page(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Update properties of an existing page."""
    page_id = arguments.get("page_id")
    properties = arguments.get("properties")

    if not page_id:
        raise HTTPException(status_code=400, detail="page_id is required")
    if not properties:
        raise HTTPException(status_code=400, detail="properties is required")

    # Build the request payload
    payload: dict[str, Any] = {
        "properties": _format_properties_for_api(properties),
    }

    # Add archived flag if provided
    if "archived" in arguments:
        payload["archived"] = arguments["archived"]

    data = await _notion_api_request(
        "PATCH",
        f"/pages/{page_id}",
        access_token,
        logger,
        json_payload=payload,
    )

    return {
        "content": [
            {
                "type": "text",
                "text": f"Updated page: {page_id}",
            }
        ],
        "isError": False,
        "_meta": {
            "page_id": data.get("id"),
            "url": data.get("url"),
            "last_edited_time": data.get("last_edited_time"),
        },
    }


async def _notion_append_blocks(
    arguments: dict[str, Any],
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    """Append content blocks to a page or block."""
    block_id = arguments.get("block_id")
    children = arguments.get("children")

    if not block_id:
        raise HTTPException(status_code=400, detail="block_id is required")
    if not children:
        raise HTTPException(status_code=400, detail="children is required")

    payload = {"children": children}

    data = await _notion_api_request(
        "PATCH",
        f"/blocks/{block_id}/children",
        access_token,
        logger,
        json_payload=payload,
    )

    block_count = len(data.get("results", []))

    return {
        "content": [
            {
                "type": "text",
                "text": f"Appended {block_count} blocks",
            }
        ],
        "isError": False,
        "_meta": {
            "block_count": block_count,
            "blocks": data.get("results", []),
        },
    }


def _format_properties_for_api(properties: dict[str, Any]) -> dict[str, Any]:
    """
    Pass through properties as-is to Notion API.

    The AI must provide properties in full Notion API format.
    No auto-conversion or smart detection - keep it simple.

    Example formats:
    - Title: {"Name": {"title": [{"text": {"content": "My Task"}}]}}
    - Rich text: {"Description": {"rich_text": [{"text": {"content": "..."}}]}}
    - Select: {"Status": {"select": {"name": "In Progress"}}}
    - Multi-select: {"Tags": {"multi_select": [{"name": "urgent"}]}}
    - Checkbox: {"Done": {"checkbox": true}}
    - Number: {"Count": {"number": 42}}
    """
    # Simple pass-through - no magic, no guessing
    return properties


async def _notion_api_request(
    method: str,
    endpoint: str,
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
    json_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a request to the Notion REST API."""
    url = f"{NOTION_API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Notion API error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            if exc.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Notion authentication failed. Reconnect the integration.",
                )
            elif exc.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Notion resource not found. Check the ID and permissions.",
                )
            else:
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"Notion API error: {exc.response.text}",
                )
        except httpx.RequestError as exc:
            logger.error("Network error calling Notion API: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Notion API. Please try again later.",
            )


def _success_response(request_id: Any, result: dict[str, Any]) -> JSONResponse:
    """Format a successful MCP JSON-RPC response."""
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }
    )


def _error_response(request_id: Any, code: int, message: str) -> JSONResponse:
    """Format an error MCP JSON-RPC response."""
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status_code=200,  # MCP uses 200 even for errors
    )
