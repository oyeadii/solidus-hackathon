from typing import Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status_code: int = 400
    status: Optional[str] = "error"
    message: Optional[str] = ""


class SuccessResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = ""
