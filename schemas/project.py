from pydantic import BaseModel
from typing import Optional, Dict


class CallRequest(BaseModel):
    prompt: str

class CallResponse(BaseModel):
    requestId: str
    traceId: str
    apiVersion: str
    service: str
    datetime: str
    isResponseImmediate: bool
    extraType: str
    response: Dict
    errorCode: Dict

class ResultRequest(BaseModel):
    taskId: str

class ResultResponse(BaseModel):
    apiVersion: str
    service: str
    datetime: str
    processDuration: Optional[float]
    isResponseImmediate: bool
    extraType: str
    response: Dict
    errorCode: Dict

class StatsResponse(BaseModel):
    apiVersion: str
    service: str
    datetime: str
    response: Dict
    errorCode: Dict

class CallbackRequest(BaseModel):
    apiVersion: str
    service: str
    datetime: str
    processDuration: float
    taskId: str
    isResponseImmediate: bool
    extraType: str
    response: Dict
    dataType: Optional[str]
    errorCode: Dict
