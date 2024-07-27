from contextlib import contextmanager
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from schemas.generic import ErrorResponse
from utilities.logger import CustomLog
from fastapi import Request


@contextmanager
def handle_errors(request: Request):
    log = CustomLog(request)
    try:
        yield
    except SQLAlchemyError as e:
        log.print_log(f"Database error: {str(e)}", level="error")
        response = ErrorResponse(
            status_code=400, status="DatabaseError", message=str(e)
        )
    except HTTPException as e:
        log.print_log(f"HTTP exception: {e.detail}", level="error")
        response = ErrorResponse(
            status_code=e.status_code, status="HTTPException", message=e.detail
        )
    except Exception as e:
        log.print_log(f"Internal server error: {str(e)}", level="error")
        response = ErrorResponse(
            status_code=500, status="InternalServerError", message=str(e)
        )
    else:
        response = None

    if response is not None:
        raise HTTPException(status_code=response.status_code, detail=vars(response))
