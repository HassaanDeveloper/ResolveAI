from typing import Dict, Any, Optional, List
from app.tools.base import BaseTool
from app.tools.schemas.base import ToolResult, ToolInput, ToolCategory


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "requires_approval": tool.requires_approval,
                "input_schema": tool.input_schema.model_json_schema() if hasattr(tool, 'input_schema') else {},
                "output_schema": tool.output_schema.model_json_schema() if hasattr(tool, 'output_schema') else {}
            }
            for tool in self._tools.values()
        ]

    def get_read_tools(self) -> List[BaseTool]:
        return [t for t in self._tools.values() if t.category == "read"]

    def get_side_effect_tools(self) -> List[BaseTool]:
        return [t for t in self._tools.values() if t.category == "side_effect"]

    async def execute(self, name: str, input_data: Dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error={"error_code": "TOOL_NOT_FOUND", "message": f"Tool '{name}' not found", "details": {}}
            )
        
        try:
            validated_input = tool.validate_input(input_data)
            return await tool.execute(validated_input)
        except Exception as e:
            return ToolResult(
                success=False,
                error={"error_code": "VALIDATION_ERROR", "message": f"Invalid input for tool '{name}': {str(e)}", "details": {}}
            )


tool_registry = ToolRegistry()