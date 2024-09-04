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
from database.db_operation.pdf_query_pro.db_operations import (
    add_user_to_users_table, 
    retrieve_user_by_field_value,
    add_pdf_document_to_db,
    retrieve_all_docs_user,
    insert_entry_to_mesasages_table,
    fetch_all_messages
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
    AWS_REGION_TEST,
    OPENAI_CREDENTIALS
)
from src.utils.exceptions import return_error_param
from src.gen_ai.rag.pinecone_operation import (
    query_by_username_dockey
)
from src.utils.aws_operation import (
    get_file
)
from src.gen_ai.rag.doc_processing import (
    init_pinecone_and_doc_indexing
)
from src.gen_ai.rag.chat_processing import (
    generate_standalone_query,
    generate_system_response
)

api_router = APIRouter()

# init s3 client
s3_client = boto3.client('s3', 
                         aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION_TEST)

#init llm 
llm = AzureChatOpenAI(
        azure_endpoint=OPENAI_CREDENTIALS['openai_api_base'],
        openai_api_version="2023-05-15",
        deployment_name="gpt-4-32k",
        openai_api_key=OPENAI_CREDENTIALS['openai_api_key'],
        openai_api_type="azure",
        temperature=0,
    )

openaiembeddings=OpenAIEmbeddings()



