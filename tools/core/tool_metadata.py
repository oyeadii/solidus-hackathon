import json
from inspect import signature
from pydantic import BaseModel
from typing import Any, Dict, Optional, Type, Callable
from .utils import create_schema_from_function


class ToolMetadata:
    def __init__(
        self,
        fn: Callable[..., Any],
        description: Optional[str] = None,
        name: Optional[str] = None,
        fn_schema: Optional[Type[BaseModel]] = None,
        return_direct: bool = False,
    ):
        self.fn = fn
        self.docstring = fn.__doc__
        self.name = name or fn.__name__
        self.description = description or f"{name}{signature(fn)}\n{self.docstring}"
        self.fn_schema = fn_schema or create_schema_from_function(
            f"{name}", fn, additional_fields=None
        )
        self.return_direct = return_direct

    def get_parameters_dict(self) -> dict:
        if self.fn_schema is None:
            parameters = {
                "type": "object",
                "properties": {
                    "input": {"title": "input query string", "type": "string"},
                },
                "required": ["input"],
            }
        else:
            parameters = self.fn_schema.model_json_schema()
            parameters = {
                k: v
                for k, v in parameters.items()
                if k in ["type", "properties", "required", "definitions"]
            }
        return parameters

    @property
    def fn_schema_str(self) -> str:
        """Get fn schema as string."""
        if self.fn_schema is None:
            raise ValueError("fn_schema is None.")
        parameters = self.get_parameters_dict()
        return json.dumps(parameters)

    def get_name(self) -> str:
        """Get name."""
        if self.name is None:
            raise ValueError("name is None.")
        return self.name

    def to_openai_tool(self) -> Dict[str, Any]:
        """To OpenAI tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_dict(),
                }
        }
