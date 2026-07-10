# Kaggle MCP Server
# Autor: Jaime Alfredo Bonilla Perez — jaimebp@gmail.com
# © 2026 Todos los derechos reservados

import sys
import json
import os
import logging
from typing import Any
from datetime import datetime

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

from kagglehub import dataset_download, competition_download, model_download, login, whoami
from kagglehub.clients import KaggleClient

logging.getLogger("kagglehub").setLevel(logging.WARNING)
logging.getLogger("kagglehub").handlers.clear()
logging.getLogger("kagglesdk").setLevel(logging.WARNING)
from kagglesdk.kaggle_env import KaggleEnv
from kagglesdk.competitions.types.competition_enums import CompetitionSortBy, HostSegment, CompetitionListTab


server = Server("kaggle-server")


CLIENT_CACHE = None


def get_client():
    global CLIENT_CACHE
    if CLIENT_CACHE is None:
        CLIENT_CACHE = KaggleClient(env=KaggleEnv.PROD)
    return CLIENT_CACHE


ENUM_MAP = {
    "sort_by": {
        "grouped": CompetitionSortBy.COMPETITION_SORT_BY_GROUPED,
        "best": CompetitionSortBy.COMPETITION_SORT_BY_BEST,
        "prize": CompetitionSortBy.COMPETITION_SORT_BY_PRIZE,
        "earliestDeadline": CompetitionSortBy.COMPETITION_SORT_BY_EARLIEST_DEADLINE,
        "latestDeadline": CompetitionSortBy.COMPETITION_SORT_BY_LATEST_DEADLINE,
        "numberOfTeams": CompetitionSortBy.COMPETITION_SORT_BY_NUMBER_OF_TEAMS,
        "recentlyCreated": CompetitionSortBy.COMPETITION_SORT_BY_RECENTLY_CREATED,
        "relevance": CompetitionSortBy.COMPETITION_SORT_BY_RELEVANCE,
    },
    "category": {
        "all": None,
        "featured": HostSegment.HOST_SEGMENT_FEATURED,
        "research": HostSegment.HOST_SEGMENT_RESEARCH,
        "recruitment": HostSegment.HOST_SEGMENT_RECRUITMENT,
        "gettingStarted": HostSegment.HOST_SEGMENT_GETTING_STARTED,
        "masters": HostSegment.HOST_SEGMENT_MASTERS,
        "playground": HostSegment.HOST_SEGMENT_PLAYGROUND,
        "community": HostSegment.HOST_SEGMENT_COMMUNITY,
        "analytics": HostSegment.HOST_SEGMENT_ANALYTICS,
    },
    "group": {
        "general": CompetitionListTab.COMPETITION_LIST_TAB_GENERAL,
        "entered": CompetitionListTab.COMPETITION_LIST_TAB_ENTERED,
        "inClass": CompetitionListTab.COMPETITION_LIST_TAB_EVERYTHING,
        "community": CompetitionListTab.COMPETITION_LIST_TAB_COMMUNITY,
        "hosted": CompetitionListTab.COMPETITION_LIST_TAB_HOSTED,
    },
}


def resolve_enum(field: str, value: str):
    mapping = ENUM_MAP.get(field)
    if mapping and value in mapping:
        return mapping[value]
    return value


def serialize(obj):
    if obj is None:
        return None
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, list):
        return [serialize(x) for x in obj]
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        result = {}
        for key in dir(obj):
            if not key.startswith("_") and not callable(getattr(obj, key)):
                try:
                    val = getattr(obj, key)
                    if val is not None and not callable(val):
                        result[key] = serialize(val)
                except Exception:
                    pass
        return result
    try:
        return str(obj)
    except Exception:
        return None


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_competitions",
            description="List Kaggle competitions with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search query to filter competitions"},
                    "category": {"type": "string", "description": "Category: all, featured, research, recruitment, gettingStarted, masters, playground, community, analytics"},
                    "sort_by": {"type": "string", "description": "Sort: grouped, best, prize, earliestDeadline, latestDeadline, numberOfTeams, recentlyCreated, relevance"},
                    "group": {"type": "string", "description": "Group: general, entered, inClass, community, hosted"},
                    "page": {"type": "integer", "description": "Page number (starts at 1)", "default": 1},
                    "page_size": {"type": "integer", "description": "Results per page", "default": 20},
                },
            },
        ),
        types.Tool(
            name="search",
            description="Search across Kaggle (competitions, datasets, kernels, models, discussions, users)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "document_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types to search: COMPETITION, DATASET, KERNEL, MODEL, DISCUSSION, USER",
                    },
                    "page_size": {"type": "integer", "description": "Results per page", "default": 10},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="list_datasets",
            description="List Kaggle datasets with optional search and filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search query to filter datasets"},
                    "page_size": {"type": "integer", "description": "Results per page", "default": 20},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                },
            },
        ),
        types.Tool(
            name="get_competition_details",
            description="Get details of a specific Kaggle competition by its ID or ref",
            inputSchema={
                "type": "object",
                "properties": {
                    "competition_ref": {"type": "string", "description": "Competition ref/slug (e.g. 'titanic', 'house-prices-advanced-regression-techniques')"},
                },
                "required": ["competition_ref"],
            },
        ),
        types.Tool(
            name="dataset_download",
            description="Download a Kaggle dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "Dataset handle (e.g. 'datasnaek/chess' or 'owner/dataset-name')"},
                    "path": {"type": "string", "description": "Optional path to a specific file within the dataset"},
                    "output_dir": {"type": "string", "description": "Output directory (defaults to cache)"},
                },
                "required": ["handle"],
            },
        ),
        types.Tool(
            name="competition_download",
            description="Download a Kaggle competition dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "competition": {"type": "string", "description": "Competition name (e.g. 'titanic', 'house-prices-advanced-regression-techniques')"},
                    "path": {"type": "string", "description": "Optional path to a specific file"},
                    "output_dir": {"type": "string", "description": "Output directory (defaults to cache)"},
                },
                "required": ["competition"],
            },
        ),
        types.Tool(
            name="model_download",
            description="Download a Kaggle model",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "Model handle (e.g. 'google/bert/tensorFlow2/bert-base-uncased')"},
                    "output_dir": {"type": "string", "description": "Output directory (defaults to cache)"},
                },
                "required": ["handle"],
            },
        ),
        types.Tool(
            name="check_auth",
            description="Check if the user is authenticated with Kaggle",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="login",
            description="Authenticate with Kaggle using an API token",
            inputSchema={
                "type": "object",
                "properties": {
                    "validate_credentials": {"type": "boolean", "description": "Whether to validate credentials", "default": True},
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        if name == "list_competitions":
            return await handle_list_competitions(arguments)
        elif name == "list_datasets":
            return await handle_list_datasets(arguments)
        elif name == "search":
            return await handle_search(arguments)
        elif name == "get_competition_details":
            return await handle_get_competition_details(arguments)
        elif name == "dataset_download":
            return await handle_dataset_download(arguments)
        elif name == "competition_download":
            return await handle_competition_download(arguments)
        elif name == "model_download":
            return await handle_model_download(arguments)
        elif name == "check_auth":
            return await handle_check_auth()
        elif name == "login":
            return await handle_login(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


def _handle_auth_error(e: Exception) -> list[types.TextContent]:
    msg = str(e)
    if "401" in msg or "Unauthorized" in msg or "not authenticated" in msg.lower():
        return [types.TextContent(type="text", text=json.dumps({
            "error": "Kaggle authentication required",
            "message": "Set up your Kaggle API credentials via:\n"
                       "1. Run the 'login' tool\n"
                       "2. Or place ~/.kaggle/kaggle.json with your API token\n"
                       "   (Get it from https://www.kaggle.com/settings -> API -> Create New Token)",
        }, ensure_ascii=False, indent=2))]
    return [types.TextContent(type="text", text=json.dumps({"error": msg}, ensure_ascii=False))]


async def handle_list_competitions(args: dict) -> list[types.TextContent]:
    try:
        client = get_client()
        from kagglesdk.competitions.types.competition_api_service import ApiListCompetitionsRequest

        request = ApiListCompetitionsRequest()
        if args.get("search"):
            request.search = args["search"]
        category = args.get("category")
        if category:
            resolved = resolve_enum("category", category)
            if resolved:
                request.category = resolved
        sort_by = args.get("sort_by")
        if sort_by:
            resolved = resolve_enum("sort_by", sort_by)
            if resolved:
                request.sort_by = resolved
        group = args.get("group")
        if group:
            resolved = resolve_enum("group", group)
            if resolved:
                request.group = resolved
        if args.get("page"):
            request.page = args["page"]
        if args.get("page_size"):
            request.page_size = args["page_size"]

        response = client.competitions.competition_api_client.list_competitions(request)
        data = serialize(response)
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2, default=str))]
    except Exception as e:
        return _handle_auth_error(e)


async def handle_list_datasets(args: dict) -> list[types.TextContent]:
    try:
        client = get_client()
        from kagglesdk.datasets.types.dataset_api_service import ApiListDatasetsRequest

        request = ApiListDatasetsRequest()
        if args.get("search"):
            request.search = args["search"]
        if args.get("page_size"):
            request.page_size = args["page_size"]
        if args.get("page"):
            request.page = args["page"]

        response = client.datasets.dataset_api_client.list_datasets(request)
        data = serialize(response)
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2, default=str))]
    except Exception as e:
        return _handle_auth_error(e)


async def handle_search(args: dict) -> list[types.TextContent]:
    try:
        client = get_client()
        from kagglesdk.search.types.search_api_service import ListEntitiesRequest, ListEntitiesFilters
        from kagglesdk.search.types.search_enums import DocumentType

        filters = ListEntitiesFilters()
        filters.query = args.get("query", "")

        doc_types = args.get("document_types", [])
        if doc_types:
            type_map = {t.upper(): getattr(DocumentType, t.upper(), None) for t in doc_types}
            filters.document_types = [v for v in type_map.values() if v is not None]

        request = ListEntitiesRequest()
        request.filters = filters
        request.page_size = args.get("page_size", 10)

        response = client.search.search_api_client.list_entities(request)
        data = serialize(response)
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2, default=str))]
    except Exception as e:
        return _handle_auth_error(e)


async def handle_get_competition_details(args: dict) -> list[types.TextContent]:
    try:
        client = get_client()
        from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest

        request = ApiGetCompetitionRequest()
        request.competition_ref = args["competition_ref"]

        response = client.competitions.competition_api_client.get_competition(request)
        data = serialize(response)
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2, default=str))]
    except Exception as e:
        return _handle_auth_error(e)


async def handle_dataset_download(args: dict) -> list[types.TextContent]:
    handle = args["handle"]
    path = args.get("path")
    output_dir = args.get("output_dir")

    result = dataset_download(handle, path=path, output_dir=output_dir)
    return [types.TextContent(type="text", text=json.dumps({"path": str(result)}, ensure_ascii=False))]


async def handle_competition_download(args: dict) -> list[types.TextContent]:
    competition = args["competition"]
    path = args.get("path")
    output_dir = args.get("output_dir")

    result = competition_download(competition, path=path, output_dir=output_dir)
    return [types.TextContent(type="text", text=json.dumps({"path": str(result)}, ensure_ascii=False))]


async def handle_model_download(args: dict) -> list[types.TextContent]:
    handle = args["handle"]
    output_dir = args.get("output_dir")

    result = model_download(handle, output_dir=output_dir)
    return [types.TextContent(type="text", text=json.dumps({"path": str(result)}, ensure_ascii=False))]


async def handle_check_auth() -> list[types.TextContent]:
    try:
        user = whoami()
        return [types.TextContent(type="text", text=json.dumps({"authenticated": True, "user": str(user)}, ensure_ascii=False))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"authenticated": False, "error": str(e)}, ensure_ascii=False))]


async def handle_login(args: dict) -> list[types.TextContent]:
    validate = args.get("validate_credentials", True)
    try:
        login(validate_credentials=validate)
        return [types.TextContent(type="text", text=json.dumps({"status": "ok", "message": "Login successful"}, ensure_ascii=False))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_opts = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_opts)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
