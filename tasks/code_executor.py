from sqlalchemy.orm import Session
from solidus.database import Task
from utilities.base_gpt import BaseGPT
from tools.functions.coder.function import JupyterCodeTool
from .prompt import ROLE, GOAL
import json


async def background_task(task_id: str, file_location: str, db: Session, question: str):
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
        base_gpt_helper = BaseGPT(tool_instances=tool_instances)
        print(f"Message Sent!!")
        async for result in base_gpt_helper._make_ai_call(messages=messages, functions=functions,):
            if result == 'data: [DONE]\n\n':
                break

            chunk = json.loads(result.replace("data:", ""))
            if chunk["type"] == "response":
                if chunk["replace"] != True:
                    output += str(chunk["content"])
                else:
                    output = str(chunk["content"])
        
        print(f"Output Recieved!!")
        task.output = output
        task.status = "completed"
        db.commit()
        print(f"Finished.")
    except Exception as e:
        print(f"Error in background task: {e}")
        task.error = str(e)
        task.status = "failed"
        db.commit()