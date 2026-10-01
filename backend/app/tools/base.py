from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel
from app.tools.schemas.base import ToolResult, ToolError


class ToolInput(BaseModel):
    pass


class ToolOutput(BaseModel):
    pass


class BaseTool(ABC):
    name: str
    category: str
    description: str
    requires_approval: bool = False
    input_schema: type[ToolInput]
    output_schema: type[ToolOutput]

    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolResult:
        pass

    def validate_input(self, input_data: dict) -> ToolInput:
        return self.input_schema(**input_data)

    def success_result(self, data: Any) -> ToolResult:
        return ToolResult(success=True, data=data.model_dump() if isinstance(data, BaseModel) else data)

    def error_result(self, error_code: str, message: str, details: dict = None) -> ToolResult:
        return ToolResult(
            success=False,
            error=ToolError(error_code=error_code, message=message, details=details or {})
        )