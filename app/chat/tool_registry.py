import logging
from collections.abc import Callable
from typing import Any

from sqlmodel import Session

from app.chat.tools.destination_tool import DestinationTool
from app.chat.tools.attraction_tool import AttractionTool
from app.chat.tools.accommodation_tool import AccommodationTool
from app.chat.tools.trekking_tool import TrekkingTool
from app.chat.tools.food_cost_tool import FoodCostTool
from app.chat.tools.budget_optimizer_tool import BudgetOptimizerTool
from app.chat.tools.route_optimizer_tool import RouteOptimizerTool
from app.chat.tools.weather_tool import WeatherTool
from app.chat.tools.flight_tool import FlightTool

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, session: Session):
        self._tools: dict[str, Callable] = {}
        self._definitions: list[dict] = []

        # Register all available tools
        self._register(DestinationTool(session))
        self._register(AttractionTool(session))
        self._register(AccommodationTool(session))
        self._register(TrekkingTool(session))
        self._register(FoodCostTool(session))
        self._register(BudgetOptimizerTool(session))
        self._register(RouteOptimizerTool(session))
        self._register(WeatherTool(session))
        self._register(FlightTool(session))
        
        logger.info(f"✅ Tool Registry initialized with {len(self._tools)} tools: {list(self._tools.keys())}")

    def _register(self, tool: Any) -> None:
        """Dynamically registers a tool's methods and definitions."""
        # 1. Register tool definitions (if the tool class provides them)
        if hasattr(tool, "get_tool_definitions"):
            self._definitions.extend(tool.get_tool_definitions())
            
        # 2. Register callable methods as executable tools
        for attr_name in dir(tool):
            if attr_name.startswith("_"):
                continue
                
            attr = getattr(tool, attr_name)
            
            # Ensure it's a callable method and not a built-in or the definition getter
            if callable(attr) and attr_name not in ("get_tool_definitions", "get_tool_name"):
                self._tools[attr_name] = attr

    def get_tool_definitions(self) -> list[dict]:
        return self._definitions

    def execute_tool(self, tool_name: str, arguments: Any) -> dict:
        """
        Executes the requested tool. 
        Includes safety checks for malformed AI arguments.
        """
        func = self._tools.get(tool_name)
        
        if not func:
            logger.warning(f"⚠️ AI tried to call an unknown tool: '{tool_name}'")
            return {"error": f"Unknown tool: {tool_name}. Available tools: {list(self._tools.keys())}"}
        
        # Safety check: Ensure arguments is a dictionary. 
        # (Qwen sometimes outputs arguments as a raw string if not strictly prompted)
        if not isinstance(arguments, dict):
            logger.warning(f"⚠️ AI passed non-dict arguments for '{tool_name}'. Attempting to parse.")
            arguments = {}

        try:
            logger.info(f"️ Executing '{tool_name}'...")
            result = func(**arguments)
            logger.info(f"✅ '{tool_name}' executed successfully.")
            return result
        except TypeError as e:
            # Catches missing or incorrect parameters passed by the AI
            logger.error(f"❌ Parameter error in '{tool_name}': {str(e)}")
            return {"error": f"Invalid parameters for {tool_name}: {str(e)}"}
        except Exception as e:
            # Catches database errors, network errors, etc.
            logger.error(f"❌ Execution error in '{tool_name}': {str(e)}")
            return {"error": f"Error executing {tool_name}: {str(e)}"}