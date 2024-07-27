import json


class FunctionDispatcher:
    def __init__(self, tool_instances):
        self.tool_instances = tool_instances

    async def dispatch(self, function_name, function_arguments):
        if function_name in self.tool_instances:
            try:
                args = json.loads(function_arguments)
            except json.JSONDecodeError:
                args = function_arguments

            tool_instance = self.tool_instances[function_name]
            try:
                method = getattr(tool_instance, tool_instance.fn_name)
                if isinstance(args, dict):
                    content, metadata = await method(**args)
                else:
                    content, metadata = await method(args)
                return content, metadata
            except Exception as e:
                raise ValueError(f"Error executing function {function_name}: {e}")
        else:
            raise ValueError(f"Function {function_name} not found")
