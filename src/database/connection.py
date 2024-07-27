import asyncpg
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

async def get_connection():
    # try:
    return await asyncpg.connect(DATABASE_URL)
    # except Exception as e:
    #     logging.info("Failed to connect to db")
    #     raise HTTPException(
    #         status_code=500,
    #         detail="Failed to connect to db"
    #     )
