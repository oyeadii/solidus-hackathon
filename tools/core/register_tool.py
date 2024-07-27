from typing import Callable
from .tool_metadata import ToolMetadata


def register_tool(name: str = None, description: str = None):
    def decorator(func: Callable):
        func._tool_metadata = ToolMetadata(fn=func, name=name, description=description)
        return func

    return decorator


def apply_tool_metadata(cls):
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and hasattr(attr, '_tool_metadata'):
            if not hasattr(cls, 'fn_name'):
                cls.fn_name = None
            if cls.fn_name is None:
                cls.fn_name = attr.__name__
            if not hasattr(cls, 'schema'):
                cls.schema = None
            if cls.schema is None:
                cls.schema = attr._tool_metadata.to_openai_tool()
    return cls
