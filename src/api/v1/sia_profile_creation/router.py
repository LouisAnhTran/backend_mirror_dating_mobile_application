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
    SingleChatMessageRequest,
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
    insert_entry_to_sia_chats_table,
    get_all_chats_by_username,
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
    extract_tag_sub_topics,
    generate_saa_greetings_for_first_user_interaction,
    generate_sia_question_to_continue_conversation,
    generate_system_response_switch_to_new_topic
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



@api_router.get("/fetch_messages/{user_name}")
async def retrieve_conversation_messages_and_start_conversation(
    user_name: str,
    authorization: Optional[str] = Header(None)
    ):

    logging.info("user_name: ",user_name)

    all_chats_by_username=await get_all_chats_by_username(
        username=user_name
    )

    logging.info("all chats by username: ",all_chats_by_username)

    # if there is no messages yet, this is the first time user interact with Saa
    if not all_chats_by_username:
        return await generate_saa_greetings_for_first_user_interaction(
            llm=llm,
            username=user_name
        )
    
    # or else user used to talk with saa before
    # we just simply continue the conversation
    user_latest_chat=all_chats_by_username[0]

    # the latest user chat always has a role of Saa
    if user_latest_chat['category_id']==0:
        return await generate_saa_greetings_for_first_user_interaction(
            llm=llm,
            username=user_name
        )
    
    logging.info("category of last time conversation is: ",user_latest_chat['category_id'])

    history_messages=[SingleChatMessageRequest(role=item['role'],
                                               content=item['content'],
                                               timestamp=item['timestamp'],
                                               category_id=item['category_id']) for item in all_chats_by_username[:10]]

    return await generate_sia_question_to_continue_conversation(
        llm=llm,
        username=user_name,
        history_messages=history_messages,
        category_id=user_latest_chat['category_id']
    )
    
    

@api_router.post("/generate_response/{user_name}")
async def saa_generate_question_or_response(
    user_name: str,
    request_body: SingleChatMessageRequest,
    authorization: Optional[str] = Header(None)
    ):

    logging.info("request_body: ",request_body)

    logging.info("user name: ",user_name)

    user_query=request_body

    if user_query.category_id==0:
        return await generate_saa_greetings_for_first_user_interaction(
            llm=llm,
            username=user_name
        )

    all_chats_by_username=await get_all_chats_by_username(
        username=user_name
    )

    history_messages=[SingleChatMessageRequest(role=item['role'],
                                               content=item['content'],
                                               timestamp=item['timestamp'],
                                               category_id=item['category_id']) for item in all_chats_by_username[1:10]]
    
    logging.info("history_messages: ",history_messages)

    # intent detection
    intent_detected=intent_detection(
        llm=llm,
        user_latest_response=user_query
    )

    logging.info("Intent detected: ",intent_detected)

    if intent_detected=="continue_conversation" or intent_detected=="greetings":
        logging.info("go inside continue conversation")

        # subtopic, and tags extracted
        if user_query.category_id:
            await extract_tag_sub_topics(
                llm=llm,
                user_latest_response=user_query.content,
                category_id=user_query.category_id,
                user_name=user_name
            )


        await insert_entry_to_sia_chats_table(
            username=user_name,
            timestamp=user_query.timestamp,
            role="user",
            content=user_query.content,
            category_id=user_query.category_id
        )


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
                category_id=user_query.category_id
            )
    
    if intent_detected=="move_to_next_category":
         return await generate_system_response_switch_to_new_topic(
                llm=llm,
                username=user_name,
                category_id=user_query.category_id+1
            )

    
    

  
        







