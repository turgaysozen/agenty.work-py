import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_db"

AGENT_ID = "your_agent_id"
AGENT_API_ENDPOINT_TEMPLATE = "https://agenty.work/api/agent/{agent_id}/chat"
AGENT_API_TOKEN = "YOUR_AGENT_API_TOKEN"