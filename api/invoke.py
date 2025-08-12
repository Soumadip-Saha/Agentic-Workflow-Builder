# /api/app.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import the specific Pydantic model for the workflow
from engine.base.workflow import WorkFlow
# Import the specific function that contains our core logic
from engine.invoke_graph import run_and_stream

from dotenv import load_dotenv

load_dotenv(".env")

app = FastAPI()

# Define the request model. FastAPI handles validation.
class InvokeRequest(BaseModel):
    workflow: WorkFlow
    query: str

# Define the API endpoint. Its only job is to route the request.
@app.post("/api/app")
async def invoke_workflow_endpoint(request: InvokeRequest):
    """
    API endpoint that receives a validated workflow and a query,
    then calls the core logic and returns its streaming response.
    """
    return StreamingResponse(
        run_and_stream(request.workflow, request.query),
        media_type="text/event-stream"
    )