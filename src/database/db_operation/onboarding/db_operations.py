import logging
import uuid
from fastapi import HTTPException
import asyncio
from typing import Union
from datetime import datetime

from src.utils.user_authentication import hash_password
from src.utils.exceptions import return_error_param
from src.database.db_connection.connection import get_connection
from src.models.requests import (
    UserSignUpRequest,
    UserSignInRequest,
    UserOnboardingRequest)

async def onboard_new_user_to_db(user: UserOnboardingRequest):
    conn=await get_connection()

    try:
        query = '''
        INSERT INTO users (username, email, industry)
        VALUES ($1, $2, $3)
        '''

        await conn.execute(query, user.username, user.email_address, user.industry)
        logging.info("Successfuly onboard user to users table")
    except Exception as e:
        logging.info("Failed to add user to users table, error message: ",e)
        raise HTTPException(status_code=500,detail="server error")
    
async def check_user_onboarding_status(email: str):
    conn=await get_connection()

    try:
        query=f'''
        select * from users as u
        where u.email=$1;
        '''

        result=await conn.fetch(query,email)

        return result
    
    except Exception as e:
        logging.info(f"Failed to check status: {e}")
        raise HTTPException(status_code=500,detail="server error")