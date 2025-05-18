from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
import os
import json
from config import STATIC_DIR
from helpers.agent_helpers import stream_agent_response

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_chat_page():
    html_file_path = os.path.join(STATIC_DIR, "chat_page.html")
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="chat_page.html not found in static directory")


@router.post("/proxy-chat")
async def proxy_chat_endpoint(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not payload.get("message"):
        raise HTTPException(status_code=400, detail="Missing 'message' in payload")

    agent_payload = {
        "message": payload.get("message"),
        "conversation_uuid": payload.get("conversation_uuid", "")
    }
    db_conn = request.app.state.db
    return StreamingResponse(stream_agent_response(agent_payload, db_conn), media_type="text/event-stream")