"""Bridge raw mcp (>=2.0.0) client sessions to LangChain tools.

langchain-mcp-adapters has no release compatible with mcp>=2.0.0 - even its
latest version imports `mcp.shared.context.RequestContext`, which the v2 SDK
removed. Until upstream catches up, these notebooks talk to MCP servers
directly through mcp's ClientSession and wrap the results as LangChain
StructuredTool objects here.
"""

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

_JSON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def jsonschema_to_pydantic(name: str, schema: dict) -> type[BaseModel]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = {}
    for field_name, field_schema in properties.items():
        py_type = _JSON_TYPE_MAP.get(field_schema.get("type"), Any)
        default = ... if field_name in required else None
        fields[field_name] = (py_type, default)
    return create_model(f"{name}_Args", **fields)


def _extract_text(result) -> str:
    return "\n".join(block.text for block in result.content if hasattr(block, "text"))


async def load_mcp_tools(session) -> list[StructuredTool]:
    listed = await session.list_tools()
    tools = []
    for tool in listed.tools:
        args_schema = jsonschema_to_pydantic(tool.name, tool.input_schema or {})

        async def _call(_tool_name=tool.name, **kwargs):
            result = await session.call_tool(_tool_name, kwargs)
            return _extract_text(result)

        tools.append(
            StructuredTool.from_function(
                name=tool.name,
                description=tool.description or "",
                args_schema=args_schema,
                coroutine=_call,
            )
        )
    return tools
