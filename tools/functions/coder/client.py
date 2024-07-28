from autogen.coding.jupyter.base import JupyterConnectionInfo
from typing_extensions import override
from autogen.coding.jupyter.jupyter_client import JupyterClient
from typing import cast


class CustomJupyterClient(JupyterClient):
    def __init__(self, connection_info: JupyterConnectionInfo):
        super().__init__(connection_info)

    @override
    def start_kernel(self, kernel_spec_name: str, folder_path: str = None) -> str:
        """Start a new kernel.

        Args:
            kernel_spec_name (str): Name of the kernel spec to start

        Returns:
            str: ID of the started kernel
        """

        payload = {"name": kernel_spec_name}
        if folder_path:
            payload["path"] = folder_path

        response = self._session.post(
            f"{self._get_api_base_url()}/api/kernels",
            headers=self._get_headers(),
            json=payload,
        )
        return cast(str, response.json()["id"])
