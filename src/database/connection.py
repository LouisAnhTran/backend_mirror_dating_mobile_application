import asyncpg
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)
 