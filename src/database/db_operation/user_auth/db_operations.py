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
    UserSignInRequest)

async def add_mobile_phone_and_otp(phone_number, otp_code):
    conn=await get_connection()

    try:
        query = '''
        INSERT INTO mobile_phone_otp_verification (phone_number, otp_code)
            VALUES ($1, $2)
            ON CONFLICT (phone_number) DO UPDATE SET otp_code = EXCLUDED.otp_code
        '''

        await conn.execute(query, phone_number, otp_code)
        logging.info("Successfuly add phone number and otp to table")
    except Exception as e:
        logging.info("Failed to add phone number and otp to table: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def insert_new_user(user: UserSignUpRequest):
    conn=await get_connection()

    try:
        query = '''
        INSERT INTO users (username, phone_number, birthday, password, email, firstname, lastname)
        VALUES ($1, $2, $3,$4,$5,$6,$7)
        '''

        hashed_password=hash_password(
            password=user.password
        )
    
        await conn.execute(query, user.username, user.phonenumber, user.birthday, hashed_password,user.email,user.firstname,user.lastname)
        logging.info("Successfuly add user to users table")
    except Exception as e:
        logging.info("Failed to add user to users table, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def retrieve_user_by_field_value(user: Union[UserSignUpRequest,UserSignInRequest],field_name,field_value):
    conn=await get_connection()

    try:
        query=f'''
        select * from users as u
        where u.{field_name}=$1;
        '''

        result=await conn.fetch(query,field_value)

        return result
    
    except Exception as e:
        logging.info(f"Failed to retrieve user by {field_name}: ",e.args)
        raise HTTPException(status_code=500,detail="server error")

async def retrieve_user_by_phoneumber(phonenumber):
    conn=await get_connection()

    try:
        query=f'''
        select * from users as u
        where u.phone_number=$1;
        '''

        result=await conn.fetch(query,phonenumber)

        return result
    
    except Exception as e:
        logging.info(f"Failed to retrieve user by {phonenumber}: ",e.args)
        raise HTTPException(status_code=500,detail="server error")

async def retrieve_otp_by_phone_number(phone_number):
    conn=await get_connection()

    try:
        query = '''
        select * from mobile_phone_otp_verification as mb
        where mb.phone_number=$1;
        '''

        result=await conn.fetch(query, phone_number)
        logging.info("Successfuly retrieve otp from phone number")

        return result
    except Exception as e:
        logging.info("Failed to query otp code from phone number: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")


async def retrieve_saa_history_chat(username):
    conn=await get_connection()

    try:
        query = '''
        select * from SaaChats as s
        where s.username=$1;
        '''

        result=await conn.fetch(query, username)
        logging.info("Successfuly retrieve history Saa messages ")

        return result
    except Exception as e:
        logging.info("Failed to retrieve history Saa messages: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")



async def add_user_to_users_table(user: UserSignUpRequest):
    conn=await get_connection()

    try:
        query = '''
        INSERT INTO users (username, password, email)
        VALUES ($1, $2, $3)
        '''

        hashed_password=hash_password(
            password=user.password
        )
    
        await conn.execute(query, user.username, hashed_password, user.email)
        logging.info("Successfuly add user to users table")
    except Exception as e:
        logging.info("Failed to add user to users table, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")



async def fetch_all_messages(
        username: str,
        docname: str,
):
    conn=await get_connection()

    try:
        query='''
        select 
            m.role,
            m.content,
            m.timestamp
        from messages as m
        where m.username=$1
        and m.doc_name=$2
        order by m.timestamp
    '''
        
        result=await conn.fetch(query,username,docname)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Database error when inserting entry to messages table"
        )
    
