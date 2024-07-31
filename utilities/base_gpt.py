import json
from solidus.config import config
from tools.core.function_dispatcher import FunctionDispatcher
from groq import AsyncGroq

class BaseGPT:
    def __init__(
        self,
        tool_instances=None,
    ):
        self.buffer = ""
        self.temperature = 0
        self.api_key = config.get("API_KEY")
        self.model_name = config.get("MODEL_NAME")
        self.client = AsyncGroq(api_key=self.api_key)

        self.dispatcher = FunctionDispatcher(tool_instances=tool_instances)

    def _build_params(
        self,
        messages,
        response_format,
        functions,
        function_call,
        parallel_tool_calls,
        is_main_call,
    ):
        params = {
            "model": self.model_name,
            "temperature": self.temperature,
            "messages": messages,
            "stream": True,
            "seed": 25,
        }
        if response_format:
            params["response_format"] = {"type": response_format}
        if functions:
            params["tools"] = functions
            params["parallel_tool_calls"] = parallel_tool_calls
        if function_call and is_main_call:
            params["tool_choice"] = function_call
        return params

    def _append_tool_calls(self, tool_calls, tcchunklist):
        for tcchunk in tcchunklist:
            while len(tool_calls) <= tcchunk.index:
                tool_calls.append(
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                )
            tc = tool_calls[tcchunk.index]
            tc["id"] += tcchunk.id or ""
            tc["function"]["name"] += tcchunk.function.name or ""
            tc["function"]["arguments"] += tcchunk.function.arguments or ""
        return tool_calls

    async def _stream_response(self, params):
        custom_return = False
        tool_calls = []

        response = await self.client.chat.completions.create(**params)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].finish_reason == 'tool_calls':
                custom_return = True
                break

            if chunk.choices and chunk.choices[0].delta.content is not None:
                current_chunk = chunk.choices[0].delta.content
                self.buffer += current_chunk
                yield (
                    custom_return,
                    self._format_response(self.buffer, current_chunk, False),
                )

            if chunk.choices and chunk.choices[0].delta.tool_calls is not None:
                tool_calls = self._append_tool_calls(
                    tool_calls, chunk.choices[0].delta.tool_calls
                )

        if custom_return:
            yield (custom_return, tool_calls)

    async def _handle_function_call(self, function_call):
        dispatcher_params = {
            "function_name": function_call["function"]["name"],
            "function_arguments": function_call["function"]["arguments"],
        }
        content, metadata = await self.dispatcher.dispatch(**dispatcher_params)
        result = {
            "tool_call_id": function_call["id"],
            "role": "tool",
            "name": function_call["function"]["name"],
            "content": str(content),
        }
        return result, metadata

    def _format_response(self, buffer, current_chunk, is_changed, type="response"):
        return f"""data: {
            json.dumps(
                {
                    "type": type,
                    "content": buffer if is_changed else current_chunk,
                    "replace": is_changed
                }
            )
        }\n\n"""

    async def _make_ai_call(
        self,
        messages: list,
        response_format=None,
        functions=None,
        function_call=None,
        parallel_tool_calls=True,
    ):
        is_main_call = True
        while True:
            params = self._build_params(
                messages,
                response_format,
                functions,
                function_call,
                parallel_tool_calls,
                is_main_call,
            )

            is_main_call = False

            function_call_detected = None
            async for result in self._stream_response(params):
                if isinstance(result, tuple):
                    custom_return, new_result = result
                    if custom_return:
                        function_call_detected = new_result
                    else:
                        yield new_result
                else:
                    raise Exception("Invalid Value.")

            if function_call_detected:
                messages.append(
                    {
                        "tool_calls": function_call_detected,
                        "role": 'assistant',
                    }
                )

                for tool_call in function_call_detected:
                    (
                        function_result,
                        function_metadata,
                    ) = await self._handle_function_call(tool_call)
                    messages.append(function_result)

                    if function_metadata[0]["function_name"] == "python":
                        self.buffer += function_metadata[0]["output"]
                        yield f"""data: {json.dumps(
                            {"content": function_metadata[0]["output"], "replace": False, "type": "response"}
                        )}\n\n"""
                        del function_metadata[0]["output"]

                    cc = json.dumps(
                        {
                            "content": function_metadata,
                            "replace": False,
                            "type": "metadata",
                        }
                    )
                    yield f"data: {cc}\n\n"
            else:
                break

        yield 'data: [DONE]\n\n'
