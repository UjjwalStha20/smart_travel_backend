from app.chat.tool_registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def get_definitions(self) -> list[dict]:
        return self.registry.get_tool_definitions()

    def execute(self, tool_name: str, arguments: dict) -> dict:
        return self.registry.execute_tool(tool_name, arguments)
