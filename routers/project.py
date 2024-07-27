from fastapi import APIRouter, HTTPException, Header, Request, Depends
from fastapi.responses import JSONResponse
import uuid
import datetime
from schemas.project import (
    CallRequest,
    CallResponse,
    ResultRequest,
    ResultResponse,
    StatsResponse,
    CallbackRequest,
)
from solidus.database import get_db


router = APIRouter(prefix="", tags=["Solidus"])


@router.post("/call")
async def create_task(
    request: CallRequest,
    x_marketplace_token: str = Header(...),
    x_request_id: str = Header(...),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...),
    db=Depends(get_db)
):
    try:
        trace_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()

        # Validate the request payload here
        if not request.method or not request.payload:
            raise HTTPException(status_code=400, detail="Invalid request payload")

        # Insert task into the database
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO tasks (id, status, created_at, method, payload)
            VALUES (?, ?, ?, ?, ?)
        ''', (task_id, 'pending', timestamp, request.method, str(request.payload)))
        db.commit()

        response = CallResponse(
            requestId=x_request_id,
            traceId=trace_id,
            apiVersion="1.0.1",
            service="AudioCraft",
            datetime=timestamp,
            isResponseImmediate=False,
            extraType="others",
            response={"taskId": task_id},
            errorCode={"status": "AC_001", "reason": "pending"}
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/result")
async def get_result(
    request: ResultRequest,
    x_marketplace_token: str = Header(...),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...),
    db=Depends(get_db)
):
    try:
        task_id = request.taskId

        cursor = db.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
        task = cursor.fetchone()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        timestamp = datetime.datetime.utcnow().isoformat()
        created_at = datetime.datetime.fromisoformat(task[2])
        processing_duration = (datetime.datetime.utcnow() - created_at).total_seconds()

        status = task[1]

        if status == "pending":
            error_code = {"status": "AC_001", "reason": "pending"}
            response_data = {"taskId": task_id}
        elif status == "in progress":
            error_code = {"status": "AC_002", "reason": "in progress"}
            response_data = {"taskId": task_id}
        elif status == "success":
            # Placeholder for actual result data retrieval
            result_data = "Result data or S3 link"
            error_code = {"status": "AC_000", "reason": "success"}
            response_data = {"dataType": "S3_OBJECT", "data": result_data}
        elif status == "failed":
            error_code = {"status": "AC_500", "reason": "failed"}
            response_data = {"taskId": task_id}
        else:
            raise HTTPException(status_code=500, detail="Unknown task status")

        response = ResultResponse(
            apiVersion="1.0.1",
            service="AudioCraft",
            datetime=timestamp,
            processDuration=processing_duration if status != "pending" else None,
            isResponseImmediate=False,
            extraType="others",
            response=response_data,
            errorCode=error_code
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stats")
async def get_stats(
    x_marketplace_token: str = Header(...),
    x_request_id: str = Header(...),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...),
    db=Depends(get_db)
):
    try:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM statistics WHERE id=1')
        stats = cursor.fetchone()

        timestamp = datetime.datetime.utcnow().isoformat()

        response = StatsResponse(
            apiVersion="1.0.1",
            service="AudioCraft",
            datetime=timestamp,
            response={
                "numRequestSuccess": stats[1],
                "numRequestFailed": stats[2]
            },
            errorCode={"status": "AC_000", "reason": "success"}
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_object(
    s3_key: str,
    x_publisher_key: str = Header(...)
):
    try:
        # Add logic to generate presigned URL for upload
        presigned_url = "https://example.com/presigned-url"

        return {
            "code": 0,
            "message": "success",
            "data": {
                "presignedUrl": presigned_url,
                "key": s3_key
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
async def download_object(
    s3_key: str,
    x_publisher_key: str = Header(...)
):
    try:
        # Add logic to generate presigned URL for download
        download_url = "https://example.com/download-url"

        return {
            "code": 0,
            "message": "success",
            "data": {
                "url": download_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete")
async def delete_object(
    s3_key: str,
    x_publisher_key: str = Header(...)
):
    try:
        # Add logic to delete object from S3
        return {
            "code": 0,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def process_callback(
    request: CallbackRequest,
    x_marketplace_token: str = Header(...),
    x_request_id: str = Header(...),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...)
):
    try:
        # Here, you can add the logic to handle the callback
        # For example, updating the status of the task in the database
        db = get_db()
        cursor = db.cursor()
        task_id = request.taskId
        status = request.errorCode["status"]
        if status == "AC_000":
            task_status = "success"
            cursor.execute('UPDATE statistics SET numRequestSuccess = numRequestSuccess + 1 WHERE id = 1')
        else:
            task_status = "failed"
            cursor.execute('UPDATE statistics SET numRequestFailed = numRequestFailed + 1 WHERE id = 1')

        cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (task_status, task_id))
        db.commit()

        return JSONResponse(status_code=201, content={"message": "Callback processed successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))