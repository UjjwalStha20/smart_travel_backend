import logging
from typing import Any

from app.chat.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def get_definitions(self) -> list[dict]:
        """Returns tool definitions (currently used for logging/testing, 
        as we inject text descriptions directly into the SYSTEM_PROMPT for Qwen)."""
        return self.registry.get_tool_definitions()

    def execute(self, tool_name: str, arguments: dict) -> Any:
        """Safely executes a tool and logs the attempt."""
        logger.info(f"🛠️ Attempting to execute tool: '{tool_name}' with args: {arguments}")
        return self.registry.execute_tool(tool_name, arguments)