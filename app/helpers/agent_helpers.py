import httpx
import asyncio
import json
from config import AGENT_ID, AGENT_API_ENDPOINT_TEMPLATE, AGENT_API_TOKEN

AGENT_API_ENDPOINT = AGENT_API_ENDPOINT_TEMPLATE.format(agent_id=AGENT_ID)
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AGENT_API_TOKEN}",
}


async def stream_agent_response(payload_for_agent: dict, db_conn):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", AGENT_API_ENDPOINT, json=payload_for_agent, headers=HEADERS) as response:
            response.raise_for_status()
            buffer = ""
            async for byte_chunk in response.aiter_bytes():
                buffer += byte_chunk.decode('utf-8', errors='replace')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        response_data_dict = json.loads(line)
                        async for sse_event_data in talk_with_your_agent(response_data_dict, db_conn):
                            if sse_event_data:
                                yield sse_event_data
                                await asyncio.sleep(0)
                                

async def talk_with_your_agent(response_data: dict, db_conn):
    if "content" in response_data:
        yield f"data: {json.dumps(response_data)}\n\n"
    elif "local_agent_info" in response_data:
        agent_info = response_data["local_agent_info"]
        agent_name = agent_info["agent_name"]
        params = agent_info["params"]
        source_name = agent_info["source_name"]
        product_id = params.get("product_id")

        if source_name == "product_table" and product_id:
            query = "SELECT * FROM public.product WHERE product_id = $1"
            db_results = await db_conn.fetch(query, product_id)

            if db_results:
                res_data_list = [dict(row) for row in db_results]
                local_data_response_payload = {
                    "local_agent_name": agent_name,
                    "local_agent_result": json.dumps(res_data_list),
                    "conversation_uuid": response_data["conversation_uuid"]
                }
                
                async for sse_event in stream_agent_response(local_data_response_payload, db_conn):
                    yield sse_event