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
    OPENAI_API_KEY
)
from src.utils.exceptions import return_error_param
from src.utils.aws_operation import (
    get_file
)
from src.gen_ai.rag_pdf.doc_processing import (
    init_pinecone_and_doc_indexing
)
from src.gen_ai.rag_pdf.chat_processing import (
    generate_standalone_query,
    generate_system_response
)

api_router = APIRouter()

# init s3 client
s3_client = boto3.client('s3', 
                         aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

openaiembeddings=OpenAIEmbeddings(
    api_key=OPENAI_API_KEY
)

@api_router.post("/user_signup")
async def user_signup(request_body: UserSignUpRequest):
    logging.info("request_body: ",request_body)

    user_by_username=await retrieve_user_by_field_value(
        user=request_body,
        field_name="username"
    )

    time.sleep(4)

    if user_by_username:
        raise HTTPException(
            status_code=403,
            detail=f"User with username {request_body.username} already existed"
        )
    
    user_by_email=await retrieve_user_by_field_value(
        user=request_body,
        field_name="email"
    )
        
    if user_by_email:
        raise HTTPException(
            status_code=403,
            detail=f"User with this email {request_body.email} already existed"
        )
    
    
    await add_user_to_users_table(
        user=request_body
    )
    
    return {"message": "User registered successfully"}

@api_router.post("/add-item")
async def add_item(
    item: dict,  # Replace with your actual item model or schema
    access_token: str = Depends(get_access_token_cookie)
):
    
    return {"message": "success"}


    
@api_router.post("/login")
async def login_for_access_token(request_body: UserSignInRequest ):
    time.sleep(4)

    user=await retrieve_user_by_field_value(
        user=request_body,
        field_name="username"
    )

    if not user:
        raise HTTPException(
            status_code=403,
            detail=f"User with username {request_body.username} does not exist, please try again"
        )
    
    user=user[0]
    if not  verify_password(
        plain_password=request_body.password,
        hashed_password=user['password']
        ):
        raise HTTPException(
            status_code=403,
            detail="Password is not correct, please try again"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/uploadfile")
async def upload_file(request: Request,
                      file: UploadFile = File(...),
       authorization: Optional[str] = Header(None)
    ):

    logging.info("authorization: ",authorization)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization token")

    access_token = authorization.split("Bearer ")[1]
    logging.info("Access token: %s", access_token)

    if access_token is None:
        raise HTTPException(status_code=401, detail="Access token is missing")

    # Verify the token and get the username
    username = decode_access_token(access_token)

    logging.info("username: ",username)
    
    folder_name=f"{username}/"

    # check if file is valid
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail={"File must be a PDF"})

    try:
        # Read file content
        file_content = await file.read()

        # Open the PDF file using PyMuPDF from the in-memory bytes
        pdf_document = fitz.open(stream=BytesIO(file_content), filetype="pdf")
        
        # Get the number of pages
        num_pages = pdf_document.page_count

        logging.info("num_pages: ",num_pages)
        
        # Get the file size
        file_size = len(file_content)

        logging.info("file_size: ",file_size)

        s3_dockey=f"{folder_name}{file.filename}"

         # insert document entry to db
        await add_pdf_document_to_db(
            s3_dockey=s3_dockey,
            username=username,
            filename=file.filename,
            pages=num_pages,
            file_size=file_size
        )

        logging.info("pass_this_stage")

        # Upload file to S3
        s3_client.put_object(
            Bucket=AWS_BUCKET_NAME_DEV,
            Key=s3_dockey,
            Body=file_content,
            ContentType=file.content_type
        )

        return {"message": "File uploaded successfully", "filename": file.filename}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=403, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(
            status_code=return_error_param(e,"status_code"), 
            detail=return_error_param(e,"detail"))
    

@api_router.get("/fetch_messages/{doc_name}")
async def retrieve_messages_from_pinecone(
    doc_name: str,
    authorization: Optional[str] = Header(None)
    ):
    logging.info("hello_in_fetch")

    # logging.info("authorization: ",authorization)

    # if not authorization or not authorization.startswith("Bearer "):
    #     raise HTTPException(status_code=401, detail="Invalid or missing Authorization token")

    # access_token = authorization.split("Bearer ")[1]
    # logging.info("Access token: %s", access_token)

    # if access_token is None:
    #     raise HTTPException(status_code=401, detail="Access token is missing")

    # Verify the token and get the username
    # username = decode_access_token(access_token)
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

@api_router.post("/generate_response/{doc_name}")
async def retrieve_messages_from_pinecone(
    doc_name: str,
    request: ChatMessagesRequest,
    authorization: Optional[str] = Header(None)
    ):
    logging.info("hello_in_fetch")

    # logging.info("authorization: ",authorization)

    # if not authorization or not authorization.startswith("Bearer "):
    #     raise HTTPException(status_code=401, detail="Invalid or missing Authorization token")

    # access_token = authorization.split("Bearer ")[1]
    # logging.info("Access token: %s", access_token)

    # if access_token is None:
    #     raise HTTPException(status_code=401, detail="Access token is missing")

    # Verify the token and get the username
    # username = decode_access_token(access_token)
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
        logging.info(f"{doc_name} has been indexed")
        # to do
        # -> fetch message from postgredb
        logging.info("requests: ",request)

        user_query=request.list_of_messages[-1]
        history_messages=request.list_of_messages[:-1]

        await insert_entry_to_mesasages_table(
            username=username,
            message=user_query.content,
            docname=doc_name,
            role=user_query.role,
            timestamp=user_query.timestamp
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

        return StreamingResponse(
            generate_system_response(
                llm=llm,
                openai_embeddings=openaiembeddings,
                standalone_query=standalone_query,
                username=username,
                history_messages=history_messages,
                doc_key=f"{username}/{doc_name}",
                top_k=10,
                doc_name=doc_name
            ), 
            media_type="text/event-stream")

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
        
    return {"data":"okie"}


# Example endpoint to fetch and return a PDF from S3
@api_router.get("/get-pdf/{file_name}")
def get_pdf(file_name: str, authorization: Optional[str] = Header(None)):
    
    logging.info("authorization: ",authorization)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization token")

    access_token = authorization.split("Bearer ")[1]

    logging.info("Access token: %s", access_token)

    if access_token is None:
        raise HTTPException(status_code=401, detail="Access token is missing")

    # Verify the token and get the username
    username = decode_access_token(access_token)

    logging.info("username: ",username)

    url=f"https://{AWS_BUCKET_NAME_DEV}.s3.{AWS_REGION_TEST}.amazonaws.com/{username}/{file_name}"

    return {"data":url}

    # # Download file from S3
    # response = s3_client.get_object(
    #         Bucket=AWS_BUCKET_NAME_DEV,
    #         Key=f"{username}/{file_name}"
    #     )

    
    # pdf_content = response['Body'].read()
        
    # # Return PDF content as a streaming response
    # return StreamingResponse(
    #         io.BytesIO(pdf_content),
    #         media_type="application/pdf",
    #         headers={"Content-Disposition": f"attachment; filename={file_name}"}
    # )



# Example endpoint to fetch and return a PDF from S3
@api_router.get("/all_docs")
async def get_all_documents_user(authorization: Optional[str] = Header(None)):
    
    logging.info("authorization: ",authorization)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization token")

    access_token = authorization.split("Bearer ")[1]

    logging.info("Access token: %s", access_token)

    if access_token is None:
        raise HTTPException(status_code=401, detail="Access token is missing")

    # Verify the token and get the username
    username = decode_access_token(access_token)

    logging.info("username: ",username)

    result=await retrieve_all_docs_user(
        username=username
    )

    time.sleep(4)


    logging.info("result ",result)

    
    return {"data":result,"message":"Fetched all files successfully"}


