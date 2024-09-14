import re
import json
import uuid
from pathlib import Path
from typing import List
from typing_extensions import override

from autogen.coding.jupyter import (
    JupyterCodeExecutor,
    JupyterConnectionInfo,
    JupyterConnectable,
)
from autogen.coding.base import CodeBlock
from autogen.coding.utils import silence_pip

from solidus.config import config
from .client import CustomJupyterClient
from ...core.register_tool import register_tool, apply_tool_metadata
from .util import IPythonCodeResult, BEFORE_INJECTING_CODE, AFTER_INJECTING_CODE
from utilities.storage_service import StorageService


@apply_tool_metadata
class JupyterCodeTool(JupyterCodeExecutor):
    def __init__(
        self,
    ):
        # JupyterCodeExecutor Init
        self._timeout = 60
        self._kernel_name = "python3"
        self._output_dir = Path(".")

        self._folder_path = f"./mntcontainer/"
        if not self._output_dir.exists():
            raise ValueError(f"Output directory {self._output_dir} does not exist.")

        self._jupyter_server = self._create_jupyter_server()

        if isinstance(self._jupyter_server, JupyterConnectable):
            self._connection_info = self._jupyter_server.connection_info
        elif isinstance(self._jupyter_server, JupyterConnectionInfo):
            self._connection_info = self._jupyter_server
        else:
            raise ValueError(
                "jupyter_server must be a JupyterConnectable or JupyterConnectionInfo."
            )

        self._jupyter_client = CustomJupyterClient(self._connection_info)
        available_kernels = self._jupyter_client.list_kernel_specs()
        if self._kernel_name not in available_kernels["kernelspecs"]:
            raise ValueError(f"Kernel {self._kernel_name} is not installed.")

        self._kernel_id = self._jupyter_client.start_kernel(
            self._kernel_name, self._folder_path
        )

        self._jupyter_kernel_client = self._jupyter_client.get_kernel_client(
            self._kernel_id
        )
        self.pattern = re.compile(r'XXXXXXXXX(.*?)XXXXXXXXX', re.DOTALL)
        self.storage_service = StorageService()

    def _create_jupyter_server(self):
        return JupyterConnectionInfo(
            host=config["PYTHON_HOST"],
            use_https=config["PYTHON_USE_HTTPS"],
            port=config["PYTHON_PORT"],
            token=config["PYTHON_TOKEN"],
        )

    @override
    async def _save_image(self, image_data_base64: str) -> str:
        """Save image data to a file."""

        file_name = f"{uuid.uuid4()}.png"

        presigned_url, key = self.storage_service.generate_presigned_upload_url(
            file_name=file_name
        )
        self.storage_service.upload_image_from_base64(
            presigned_url=presigned_url, 
            base64_string=image_data_base64
        )
        image_url = self.storage_service.generate_presigned_download_url(
            key=key
        )
        return image_url

    @override
    async def _save_html(self, html_data: str) -> str:
        """Save html data to a file."""
        return html_data

    async def generate_and_return_plot_json(self, code):
        try:
            new_code = BEFORE_INJECTING_CODE
            new_code += code
            new_code += AFTER_INJECTING_CODE

            result = await self.execute_code_blocks(
                code_blocks=[
                    CodeBlock(language="python", code=new_code),
                ],
                from_self=True,
            )

            match = self.pattern.search(result.output)

            if match:
                fig_dicts = json.loads(match.group(1).strip())
            else:
                fig_dicts = [{}]

        except Exception as e:
            fig_dicts = [{"error": str(e)}]

        return fig_dicts

    @override
    async def execute_code_blocks(
        self,
        code_blocks: List[CodeBlock],
        from_self=False,
    ) -> IPythonCodeResult:
        """(Experimental) Execute a list of code blocks and return the result.

        This method executes a list of code blocks as cells in the Jupyter kernel.
        See: https://jupyter-client.readthedocs.io/en/stable/messaging.html
        for the message protocol.

        Args:
            code_blocks (List[CodeBlock]): A list of code blocks to execute.

        Returns:
            IPythonCodeResult: The result of the code execution.
        """
        self._jupyter_kernel_client.wait_for_ready()
        outputs = []
        output_files = []
        for code_block in code_blocks:
            code = silence_pip(code_block.code, code_block.language)
            result = self._jupyter_kernel_client.execute(
                code, timeout_seconds=self._timeout
            )
            if result.is_ok:
                plot_json_data = None
                plot_json_index = 0

                outputs.append(result.output)
                for data in result.data_items:
                    if not from_self:
                        if data.mime_type == "image/png":
                            path = await self._save_image(data.data)
                            outputs.append("File Created Successfully!!")

                            # if plot_json_data is None or plot_json_index >= len(
                            #     plot_json_data
                            # ):
                            #     plot_json_data = (
                            #         await self.generate_and_return_plot_json(code=code)
                            #     )
                            #     plot_json_index = 0

                            output_files.append({"url": path})
                            plot_json_index += 1

                        elif data.mime_type == "text/html":
                            # outputs.append(data.data)
                            pass
                        else:
                            outputs.append(json.dumps(data.data))
                    else:
                        if data.mime_type == "image/png":
                            pass
                        elif data.mime_type == "text/html":
                            pass
                        else:
                            outputs.append(json.dumps(data.data))
            else:
                return IPythonCodeResult(
                    exit_code=1,
                    output=f"ERROR: {result.output}",
                )

        return IPythonCodeResult(
            exit_code=0,
            output="\n".join([str(output) for output in outputs]),
            output_files=output_files,
        )

    @register_tool(
        name="python",
        description="Use this tool to execute any Python code for tasks such as:\n- **Performing calculations:** From simple arithmetic to complex mathematical operations, handle all your computational needs efficiently.\n- **Analyzing data:** Process, clean, and analyze data sets to uncover insights and trends using powerful Python libraries.\n- **Generating visualizations:** Create a wide range of visual representations, including charts and graphs, to effectively communicate your data findings.",
    )
    async def execute_code(self, code: str):
        """
        Executes the given Python code on the connected Jupyter server.

        Args:
            code (str): The Python code to be executed.

        Returns:
            result: The result of the executed code.
        """
        result = await self.execute_code_blocks(
            code_blocks=[
                CodeBlock(language="python", code=code),
            ]
        )

        metadata = [
            {
                "code": code,
                "output_files": [list(d.values())[0] for d in result["output_files"]],
                "output": f"\n\n<details>\n\n<summary>Analyzing...</summary>\n\n```python\n{code}\n```\n\n```output\n{result.output}\n```\n\n</details>\n\n",
                "function_name": "python",
            }
        ]
        return {"input": code, "output": result.output}, metadata
