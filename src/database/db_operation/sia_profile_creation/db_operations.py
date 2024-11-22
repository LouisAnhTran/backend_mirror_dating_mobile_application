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

async def insert_entry_to_sia_chats_table(
        username: str,
        content: str,
        role: str, 
        timestamp: datetime,
        category_id: int
):
    conn=await get_connection()

    try:
        query='''
            insert into SaaChats (username,timestamp,content,role,category_id) values($1,$2,$3,$4,$5)
        '''

        await conn.execute(query, username, timestamp, content,role,category_id)
        logging.info("Successfuly add message to sia chats table")
    except Exception as e:
        logging.info("Failed to add message to sia chats table, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def add_subtopics_as_payload_to_categories_for_update_user_profile(
        username: str,
        category_id: int,
        payload: str
):
    conn=await get_connection()

    try:
        query='''
            UPDATE Categories
            SET payload = $1
            WHERE username = $2 AND category_id = $3;
        '''

        await conn.execute(query, payload,username,category_id)
        logging.info("Successfuly update payload")
    except Exception as e:
        logging.info("Failed to update payload: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def get_all_chats_by_username(
        username: str,
):
    conn=await get_connection()

    try:
        query='''
            select * 
            from SaaChats as s
            where s.username = $1
            order by s.timestamp desc;
        '''

        results=await conn.fetch(query, username)

        logging.info("Successfuly retrieve all chats for a user")

        return results
    except Exception as e:
        logging.info("Failed to retrieve all chats for a user, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def get_all_categories_by_username(
        username: str,
):
    conn=await get_connection()

    try:
        query='''
            select * 
            from Categories as c
            where c.username = $1;
        '''

        results=await conn.fetch(query, username)

        logging.info("Successfuly retrieve all catefories for a user")

        return results
    except Exception as e:
        logging.info("Failed to retrieve all catefories for a user, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def get_category_by_username_and_id(
        username: str,
        category_id: int
):
    conn=await get_connection()

    try:
        query='''
            select * 
            from Categories as c
            where c.username = $1 and c.category_id=$2;
        '''

        results=await conn.fetch(query, username, category_id)

        logging.info("Successfuly retrieve all catefories for a user")

        return results
    except Exception as e:
        logging.info("Failed to retrieve all catefories for a user, error message: ",e.args[0])
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

    
async def retrieve_user_by_field_value(user: Union[UserSignUpRequest,UserSignInRequest],field_name):
    conn=await get_connection()

    try:
        query=f'''
        select * from users as u
        where u.{field_name}=$1;
        '''

        result=await conn.fetch(query,field_name)

        return result
    
    except Exception as e:
        logging.info(f"Failed to retrieve user by {field_name}: ",e.args)
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