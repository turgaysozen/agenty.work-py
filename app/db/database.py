import asyncpg
from app.config import DATABASE_URL

async def connect_db():
    connection = await asyncpg.connect(DATABASE_URL)
    return connection

async def close_db(connection):
    if connection:
        await connection.close()