# import httpx
# import asyncio
# import json
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import StreamingResponse, HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# import os
# import asyncpg

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# STATIC_DIR = os.path.join(BASE_DIR, "static")
# if not os.path.exists(STATIC_DIR):
#     os.makedirs(STATIC_DIR)

# app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/test_db"


# @app.on_event("startup")
# async def startup():
#     app.state.db = await asyncpg.connect(DATABASE_URL)


# @app.on_event("shutdown")
# async def shutdown():
#     await app.state.db.close()


# agent_id = "your_agent_id"
# AGENT_API_ENDPOINT = f"https://agenty.work/api/agent/{agent_id}/chat"
# AGENT_API_TOKEN = "YOUR_AGENT_API_TOKEN"
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {AGENT_API_TOKEN}",
# }


# async def stream_agent_response(payload_for_agent: dict):
#     async with httpx.AsyncClient(timeout=None) as client:
#         async with client.stream("POST", AGENT_API_ENDPOINT, json=payload_for_agent, headers=headers) as response:
#             response.raise_for_status()
#             buffer = ""
#             async for byte_chunk in response.aiter_bytes():
#                 buffer += byte_chunk.decode('utf-8', errors='replace')
#                 while '\n' in buffer:
#                     line, buffer = buffer.split('\n', 1)
#                     if line.strip():
#                         async for sse_event_data in talk_with_your_agent(line):
#                             if sse_event_data:
#                                 yield sse_event_data
#                                 await asyncio.sleep(0) 

                            
# async def talk_with_your_agent(line: str):
#     response_data = json.loads(line)

#     if "content" in response_data:
#         yield f"data: {json.dumps(response_data)}\n\n"
#     elif "local_agent_info" in response_data:
#         agent_info = response_data["local_agent_info"]
#         agent_name = agent_info["agent_name"]
#         params = agent_info["params"]
#         source_name = agent_info["source_name"] # can be dict like {"product_id": 123, "status": "active"}
#         product_id = params.get("product_id")

#         if source_name == "product_table" and product_id:
#             query = "SELECT * FROM public.product WHERE product_id = $1"
#             db_results = await app.state.db.fetch(query, product_id)

#             if db_results:
#                 res_data_list = [dict(row) for row in db_results]
#                 local_data_response_payload = {
#                     "local_agent_name": agent_name,
#                     "local_agent_result": json.dumps(res_data_list),
#                     "conversation_uuid": response_data["conversation_uuid"]
#                 }
                
#                 async for sse_event in stream_agent_response(local_data_response_payload):
#                     yield sse_event



# @app.get("/", response_class=HTMLResponse)
# async def get_chat_page():
#     html_file_path = os.path.join(STATIC_DIR, "chat_page.html")
#     try:
#         with open(html_file_path, "r", encoding="utf-8") as f:
#             html_content = f.read()
#         return HTMLResponse(content=html_content)
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="chat_page.html not found in static directory")



# @app.post("/proxy-chat")
# async def proxy_chat_endpoint(request: Request):
#     try:
#         payload = await request.json()
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid JSON payload")

#     if not payload.get("message"):
#         raise HTTPException(status_code=400, detail="Missing 'message' in payload")

#     agent_payload = {
#         "message": payload.get("message"),
#         "conversation_uuid": payload.get("conversation_uuid", "")
#     }
#     return StreamingResponse(stream_agent_response(agent_payload), media_type="text/event-stream")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
    



from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

from app.api.endpoints import router as api_router
from app.db.database import connect_db, close_db
from app.config import STATIC_DIR

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
async def startup_event():
    app.state.db = await connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, 'db') and app.state.db:
        await close_db(app.state.db)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)