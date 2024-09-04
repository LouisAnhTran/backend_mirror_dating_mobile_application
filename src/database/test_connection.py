import asyncpg
import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config import DATABASE_URL

# Load environment variables from .env file
load_dotenv()

async def test_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Connection successful")
    finally:
        await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
