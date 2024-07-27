import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

async def test_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Connection successful")
    finally:
        await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
