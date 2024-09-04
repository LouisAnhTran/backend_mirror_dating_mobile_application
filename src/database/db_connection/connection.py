import asyncpg
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

from src.config import DATABASE_URL

load_dotenv()

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)
 