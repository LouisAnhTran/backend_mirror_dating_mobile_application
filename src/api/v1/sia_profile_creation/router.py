from fastapi import APIRouter, Depends, HTTPException, Cookie, File, UploadFile, Request, Header
from typing import List
from logging_config import logger
import logging
import time 
from datetime import datetime, timedelta 
from typing import Optional
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import fitz
from io import BytesIO
from fastapi.responses import StreamingResponse
import io
from langchain_openai import OpenAI
from langchain_community.chat_models import AzureChatOpenAI
from fastapi.responses import StreamingResponse
from langchain_community.embeddings import AzureOpenAIEmbeddings
from langchain.embeddings import OpenAIEmbeddings


from src.models.requests import (
    UserSignUpRequest,
    UserSignInRequest,
    FetchChatMessagesRequest,
    ChatMessagesRequest)
from src.utils.user_authentication import create_access_token
from src.database.db_operation.pdf_query_pro.db_operations import (
    add_user_to_users_table, 
    retrieve_user_by_field_value,
    add_pdf_document_to_db,
    retrieve_all_docs_user,
    insert_entry_to_mesasages_table,
    fetch_all_messages
)
from src.database.db_operation.sia_profile_creation.db_operations import (
    insert_entry_to_sia_chats_table
)
from src.utils.user_authentication import (
    hash_password,
    verify_password,
    get_access_token_cookie,
    decode_access_token
    )
from src.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AWS_ACCESS_KEY,
    AWS_SECRET_ACCESS_KEY,
    AWS_BUCKET_NAME_DEV,
    AWS_REGION,
    GPT4_OPENAI_API_KEY,
    GTP4_OPENAI_API_BASE,
    OPENAI_API_KEY
)
from src.utils.exceptions import return_error_param
from src.gen_ai.rag_pdf.pinecone_operation import (
    query_by_username_dockey
)
from src.utils.aws_operation import (
    get_file
)
from src.gen_ai.sia_engine.chat_processing import (
    generate_standalone_query,
    generate_system_response,
    intent_detection,
    extract_tag_sub_topics
)


api_router = APIRouter()


#init llm 
llm = AzureChatOpenAI(
        azure_endpoint=GTP4_OPENAI_API_BASE,
        openai_api_version="2023-05-15",
        deployment_name="gpt-4-32k",
        openai_api_key=GPT4_OPENAI_API_KEY,
        openai_api_type="azure",
        temperature=0,
    )

openaiembeddings=OpenAIEmbeddings(
    api_key=OPENAI_API_KEY
)



@api_router.get("/fetch_messages/{doc_name}")
async def retrieve_messages_from_pinecone(
    doc_name: str,
    authorization: Optional[str] = Header(None)
    ):
    logging.info("hello_in_fetch")

    username='louis_anh_tran'

    logging.info("username: ",username)

    # check if we indexing for this document or not
    result=query_by_username_dockey(
        username=username,
        doc_key=f"{username}/{doc_name}",
        query="test",
        top_k=1
    )


    logging.info("result_query_pinecone: ",result)

    if result:
        all_messages=await fetch_all_messages(
            username=username,
            docname=doc_name
        )

        logging.info("all_messages: ",all_messages)

        return {"data":all_messages}

    else:
        # to do
        logging.info("start_pinecone_indexing")
        # retrieve pdf from aws
        file_content= get_file(
            s3_client=s3_client,
            doc_key=f"{username}/{doc_name}"
        )[0]

        logging.info("file_content: ",file_content)

        # run pinecone indexing pineline
        try:
            init_pinecone_and_doc_indexing(
            username=username,
            doc_key=f"{username}/{doc_name}",
            file_bytes=file_content
        )
        except Exception as e:
            raise HTTPException(status_code=500,
                                detail="We encouter error when spinning up chat engine for this document")
        
    return {"data":[]}

@api_router.post("/generate_response/{user_name}")
async def retrieve_messages_from_pinecone(
    user_name: str,
    request_body: ChatMessagesRequest,
    authorization: Optional[str] = Header(None)
    ):

    logging.info("request_body: ",request_body)

    logging.info("user name: ",user_name)

    user_query=request_body.list_of_messages[-1]
    history_messages=request_body.list_of_messages[:-1]

    # intent detection
    intent_detected=intent_detection(
        llm=llm,
        user_latest_response=user_query
    )

    logging.info("Intent detected: ",intent_detected)

    
    # subtopic, and tags extracted
    if request_body.category_id:
        await extract_tag_sub_topics(
            llm=llm,
            user_latest_response=user_query.content,
            category_id=request_body.category_id,
            user_name=user_name
        )


    await insert_entry_to_sia_chats_table(
        username=user_name,
        timestamp=user_query.timestamp,
        role="user",
        content=user_query.content
    )

    logging.info("user_query: ",user_query)
    logging.info("history_messages: ",history_messages)

    if not history_messages:
        standalone_query=user_query.content
    else:
        standalone_query=generate_standalone_query(
            llm=llm,
            user_query=user_query,
            history_messages=history_messages
        )

    logging.info("pass this stage")

    return await generate_system_response(
            llm=llm,
            openai_embeddings=openaiembeddings,
            standalone_query=standalone_query,
            username=user_name,
            history_messages=history_messages, 
        )

  
        







