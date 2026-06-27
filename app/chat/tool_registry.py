from sqlmodel import Session

from app.chat.tools.destination_tool import DestinationTool
from app.chat.tools.attraction_tool import AttractionTool
from app.chat.tools.accommodation_tool import AccommodationTool
from app.chat.tools.trekking_tool import TrekkingTool
from app.chat.tools.food_cost_tool import FoodCostTool


class ToolRegistry:
    def __init__(self, session: Session):
        self._tools = {}
        self._definitions = []

        self._register(DestinationTool(session))
        self._register(AttractionTool(session))
        self._register(AccommodationTool(session))
        self._register(TrekkingTool(session))
        self._register(FoodCostTool(session))

    def _register(self, tool):
        if hasattr(tool, "get_tool_definitions"):
            self._definitions.extend(tool.get_tool_definitions())
        for attr_name in dir(tool):
            if attr_name.startswith("_"):
                continue
            attr = getattr(tool, attr_name)
            if callable(attr) and attr_name not in ("get_tool_definitions",):
                self._tools[attr_name] = attr

    def get_tool_definitions(self) -> list[dict]:
        return self._definitions

    def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        func = self._tools.get(tool_name)
        if not func:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return func(**arguments)
        except Exception as e:
            return {"error": f"Error executing {tool_name}: {str(e)}"}
