"""Tool registry — unified access to all LLM-callable tools."""

from core.tools.crm_tools import CRM_TOOL_DEFINITIONS, CRM_TOOL_HANDLERS
from core.tools.erp_tools import ERP_TOOL_DEFINITIONS, ERP_TOOL_HANDLERS
from core.tools.whatsapp_tools import WHATSAPP_TOOL_DEFINITIONS, WHATSAPP_TOOL_HANDLERS

# All tool definitions for OpenAI function calling
ALL_TOOL_DEFINITIONS = (
    CRM_TOOL_DEFINITIONS + ERP_TOOL_DEFINITIONS + WHATSAPP_TOOL_DEFINITIONS
)

# All tool handlers mapped by function name
ALL_TOOL_HANDLERS = {
    **CRM_TOOL_HANDLERS,
    **ERP_TOOL_HANDLERS,
    **WHATSAPP_TOOL_HANDLERS,
}


async def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a tool by name with the given arguments."""
    handler = ALL_TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    try:
        return await handler(**arguments)
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
