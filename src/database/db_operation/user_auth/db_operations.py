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
        INSERT INTO users (username, phone_number, birthday, password)
        VALUES ($1, $2, $3,$4)
        '''

        hashed_password=hash_password(
            password=user.password
        )
    
        await conn.execute(query, user.username, user.phonenumber, user.birthday, hashed_password)
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

async def retrieve_some_ai_tools_for_all_catogories(
        number: int,
        category: str
):
    conn=await get_connection()

    try:
        query = '''
        WITH RankedItems AS (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY at.category ORDER BY at.popularity DESC) AS rn
        FROM
            ai_tools as at
        )
        SELECT
            *
        FROM
            RankedItems as ri
        WHERE
            rn <= $1
            and category = $2;
        '''

 
        result=await conn.fetch(query, number,category)
        logging.info("Successfuly add user to users table")

        return result
    except Exception as e:
        logging.info("Failed retrieve_some_ai_tools_for_all_catogories: ",e)
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

    

async def find_pdf_document_by_s3_dockey(
        s3_dockey: str
):
    try:
        conn=await get_connection()

        query='''
            select *
            from documents as d
            where d.s3_dockey=$1;
        '''

        result= await conn.fetch(query,s3_dockey)
        
        return result
    except Exception as e:
        logging.info("Failed to find document by s3 dockey")
        raise HTTPException(
            status_code=500,
            detail="Failed to perform db operations"
        )

async def add_pdf_document_to_db(s3_dockey: str,
                                 username: str,
                                 filename: str,
                                 pages: int,
                                 file_size: float):
    try:
        conn=await get_connection()

        doc=await find_pdf_document_by_s3_dockey(
            s3_dockey=s3_dockey
        )

        logging.info("doc_doc ",doc)

        if doc:
            raise HTTPException(
                status_code=409,
                detail=f"Document with {s3_dockey} aleady exist for username {username}"
            )

        query='''
            insert into documents(s3_dockey,doc_name,username,no_of_pages,doc_size)
            values($1,$2,$3,$4,$5);
        '''

        await conn.execute(query,
                           s3_dockey,
                           filename,
                           username,
                           pages,
                           file_size)
        
        logging.info("Successully add pdf document to df")
    except Exception as e:
        logging.info("Failed to add pdf document to db ",e.status_code)
        raise HTTPException(
            status_code=return_error_param(e,"status_code"),
            detail=return_error_param(e,"detail")
        )
    
async def retrieve_all_docs_user(username: str):
    try:
        conn=await get_connection()

        query='''
            select 
                d.doc_name, d.no_of_pages, d.doc_size, d.uploaded_time
            from documents as d
            where d.username=$1;
        '''

        result=await conn.fetch(query,
                           username)
        
        logging.info("Successully add pdf document to df")

        return result
    except Exception as e:
        logging.info("Failed to fetch pdf document to db ",e.status_code)
        raise HTTPException(
            status_code=return_error_param(e,"status_code"),
            detail=return_error_param(e,"detail")
        )
    
async def insert_entry_to_mesasages_table(
        username: str,
        message: str,
        docname: str,
        role: str, 
        timestamp: datetime
):
    conn=await get_connection()

    # try:
    query='''
    insert into messages (doc_name,username,role,content,timestamp) values($1,$2,$3,$4,$5)
'''
    
    await conn.execute(query,docname,username,role,message,timestamp)
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail="Database error when inserting entry to messages table"
    #     )
    
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