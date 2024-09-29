import json
from solidus.config import config
from tools.core.function_dispatcher import FunctionDispatcher
from openai import AsyncOpenAI
from groq import AsyncGroq

class BaseGPT:
    def __init__(
        self,
        tool_instances=None,
    ):
        self.buffer = ""
        self.temperature = 0
        self.api_key = config.get("SAMBANOVA_API_KEY")
        # self.api_key = config.get("API_KEY")
        self.model_name = config.get("SAMBANOVA_MODEL_NAME")
        # self.model_name = config.get("MODEL_NAME")
        # self.client = AsyncOpenAI(api_key=self.api_key)
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=config.get("BASE_URL"))

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

    # async def _stream_response(self, params):
    #     custom_return = False
    #     tool_calls = []

    #     response = await self.client.chat.completions.create(**params)
    #     async for chunk in response:
    #         print(chunk)
    #         if chunk.choices and chunk.choices[0].finish_reason == 'tool_calls':
    #             custom_return = True
    #             break

    #         if chunk.choices and chunk.choices[0].delta.content is not None:
    #             current_chunk = chunk.choices[0].delta.content
    #             self.buffer += current_chunk
    #             yield (
    #                 custom_return,
    #                 self._format_response(self.buffer, current_chunk, False),
    #             )

    #         if chunk.choices and chunk.choices[0].delta.tool_calls is not None:
    #             tool_calls = self._append_tool_calls(
    #                 tool_calls, chunk.choices[0].delta.tool_calls
    #             )

    #     if custom_return:
    #         yield (custom_return, tool_calls)

    async def _stream_response(self, params):
        custom_return = False
        tool_calls = []
        code_block_start_pattern = r'```python\s*'  # Pattern for start of Python code block
        code_block_end_pattern = r'```'  # Pattern for end of code block

        self.buffer = ""
        
        response = await self.client.chat.completions.create(**params)
        
        async for chunk in response:
            # print(chunk)
            if chunk.choices and chunk.choices[0].delta.content is not None:
                current_chunk = chunk.choices[0].delta.content
                self.buffer += current_chunk

                # Check if the buffer contains both start and end of a code block
                start_index = self.buffer.find("```python")
                end_index = self.buffer.find("```", start_index + len("```python"))

                # If both start and end of code block are found
                if start_index != -1 and end_index != -1:
                    # Extract code between the markers
                    extracted_code = self.buffer[start_index + len("```python"):end_index].strip()
                    
                    # Add the code as a tool call
                    tool_calls.append({
                        "id": f"code_{len(tool_calls) + 1}",
                        "type": "function",
                        "function": {
                            "name": "python",
                            "arguments": extracted_code
                        }
                    })
                    # print(tool_calls)
                    
                    # Remove the processed code block from the buffer
                    self.buffer = self.buffer[end_index + len("```"):]
                    
                    # Set custom_return to True when a complete code block is found
                    custom_return = True

                # Yield current state of the buffer and chunk
                yield (
                    custom_return,
                    self._format_response(self.buffer, current_chunk, False),
                )

            # Reset custom_return to False if no more complete code blocks in buffer
            if custom_return:
                custom_return = False
                yield (True, tool_calls)

        # Final check if there are any pending tool calls
        if custom_return or tool_calls:
            yield (True, tool_calls)

    async def _handle_function_call(self, function_call):
        dispatcher_params = {
            "function_name": function_call["function"]["name"],
            "function_arguments": function_call["function"]["arguments"],
        }
        content, metadata = await self.dispatcher.dispatch(**dispatcher_params)
        result = {
            # "tool_call_id": function_call["id"],
            "role": "ipython",
            # "name": function_call["function"]["name"],
            "content": str(content),
        }
        # result= str(content)
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
        parallel_tool_calls=False,
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
                        "content": function_call_detected,
                        "role": 'assistant',
                    }
                )

                for tool_call in function_call_detected:
                    (
                        function_result,
                        function_metadata,
                    ) = await self._handle_function_call(tool_call)
                    messages.append(function_result)
                    print(messages,"\nmessages\n")

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
