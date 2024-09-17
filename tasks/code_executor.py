from sqlalchemy.orm import Session
from solidus.database import Task
from utilities.base_gpt import BaseGPT
from tools.functions.coder.function import JupyterCodeTool
from .prompt import ROLE, GOAL
import json

import time
import requests
import datetime
import uuid

############### ADD THE AI MARKETPLACE WEBHOOK ENDPOINT HERE ###############
# webhook_url = "http://localhost:8000/callback"
webhook_url = "https://mkpl-user.staging.devsaitech.com/api/v1/ai-connection/callback"



async def background_task(task_id: str, file_location: str, db: Session, question: str):

    start_time = time.time()

    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        print(f"Task Started {task.id}")
        tool_instances = {'python': JupyterCodeTool()}
        functions = [fn.schema for fn in tool_instances.values()]

        messages = [{"role": "system", "content": ROLE}]
        messages.append(
            {
                "role": "user",
                "content": GOAL.format(question=question, file_location=file_location),
            }
        )

        output = ""
        image_urls = []
        base_gpt_helper = BaseGPT(tool_instances=tool_instances)
        print(f"Message Sent!!")
        async for result in base_gpt_helper._make_ai_call(
            messages=messages,
            functions=functions,
        ):
            if result == 'data: [DONE]\n\n':
                break

            chunk = json.loads(result.replace("data:", ""))
            if chunk["type"] == "response":
                if chunk["replace"] != True:
                    output += str(chunk["content"])
                else:
                    output = str(chunk["content"])
            elif chunk["type"] == "metadata":
                metadata = chunk["content"]
                for mt in metadata:
                    if mt["output_files"]:
                        image_urls.extend(mt["output_files"])


        print(f"Output Recieved!!")
        task.output = output
        task.files = image_urls
        task.status = "completed"
        db.commit()
        print(f"Finished.")

        end_time = time.time()
        processing_duration = end_time - start_time
        print(processing_duration)

        if image_urls:
            text_data = [{"dataType": "METADATA", "data": output}]
            image_urls_data = [{"dataType": "S3_OBJECT", "data": result} for result in image_urls]
            datatype = "HYBRID"
            data = text_data + image_urls_data
        else:
            datatype = "METADATA"
            data = output
        

        send_callback(task_id,processing_duration, data, datatype)

        
    except Exception as e:
        print(f"Error in background task: {e}")
        task.error = str(e)
        task.status = "failed"
        db.commit()

def send_callback(task_id, processing_duration, data, datatype):
    
    user_id = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    callback_message = {
        "apiVersion": "0.1.0",
        "service": "P&L Analyser",
        "datetime": datetime.datetime.now().isoformat(),
        "processDuration": processing_duration,  # Simulated duration
        "taskId": task_id,
        "isResponseImmediate": False,
        "response": {
            "dataType": datatype,
            "data": data
        },
        "errorCode": {
            "status": "AC_000",
            "reason": "success"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-marketplace-token": "1df239ef34d92aa8190b8086e89196ce41ce364190262ba71964e9f84112bc45",
        "x-request-id": requestId,
        "x-user-id": user_id
    }

    response = requests.post(webhook_url, json=callback_message, headers=headers)
    print(response.json())

