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
from pydantic import BaseModel
import random
from twilio.rest import Client


from src.models.requests import (
    UserSignUpRequest,
    UserSignInRequest,
    FetchChatMessagesRequest,
    ChatMessagesRequest,
    UserOnboardingRequest,
    OTPRequest,
    OTPVerification,
    SignInByEmail)
from src.utils.user_authentication import create_access_token
from src.database.db_operation.pdf_query_pro.db_operations import (
    add_user_to_users_table, 
    add_pdf_document_to_db,
    retrieve_all_docs_user,
    insert_entry_to_mesasages_table,
    fetch_all_messages
)
from src.database.db_operation.user_auth.db_operations import (
    add_mobile_phone_and_otp,
    retrieve_otp_by_phone_number,
    insert_new_user,
    retrieve_user_by_field_value
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
    OPENAI_API_KEY,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER
)
from src.utils.exceptions import return_error_param
from src.gen_ai.rag_pdf.pinecone_operation import (
    query_by_username_dockey
)
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
from src.database.db_operation.onboarding.db_operations import (
    onboard_new_user_to_db,
    check_user_onboarding_status
)

api_router = APIRouter()

# Twilio configuration
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# In-memory OTP storage (consider using a database in production)
otp_store = {}

# init s3 client
s3_client = boto3.client('s3', 
                         aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

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


@api_router.post("/generate-otp")
async def generate_otp(request: OTPRequest):
    # Generate a random 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Store OTP in memory with the associated phone number (use a database for production)
    await add_mobile_phone_and_otp(request.phone_number,otp)

    logger.info("otp: ",request.phone_number)
    
    time.sleep(3)


    # Send OTP via Twilio
    try:
        message = client.messages.create(
            body=f"Your verification code is {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=request.phone_number
        )
        return {"status": "OTP sent successfully"}
    except Exception as e:
        print(f"Twilio error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP") from e

@api_router.post("/sign-in-phone-number-generate-otp")
async def generate_otp(request: OTPRequest):
    # check if user already register
    user_by_phone=await retrieve_user_by_field_value(
        user=request,
        field_name="phone_number",
        field_value=request.phone_number
    )

    logging.info("user by phone: ",user_by_phone)

    if not user_by_phone:
        raise HTTPException(status_code=403, detail="This phonenumber is not registered, please sign up first") 

    # Generate a random 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Store OTP in memory with the associated phone number (use a database for production)
    await add_mobile_phone_and_otp(request.phone_number,otp)

    logger.info("otp: ",request.phone_number)
    
    time.sleep(3)


    # Send OTP via Twilio
    try:
        message = client.messages.create(
            body=f"Your verification code is {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=request.phone_number
        )
        return {"status": "OTP sent successfully"}
    except Exception as e:
        print(f"Twilio error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP") from e

@api_router.post("/sign-in-by-email")
async def generate_otp(request_body: SignInByEmail):
    time.sleep(4)

    logging.info("request_body: ",request_body)

    user=await retrieve_user_by_field_value(
        user=request_body,
        field_name="username",
        field_value=request_body.email
    )

    if not user:
        user=await retrieve_user_by_field_value(
            user=request_body,
            field_name="email",
            field_value=request_body.email
        )

        if not user:
            raise HTTPException(
                status_code=403,
                detail=f"Username or phone number does not exist, please try again"
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


@api_router.post("/verify-otp")
async def verify_otp(verification: OTPVerification):
    stored_otp = await retrieve_otp_by_phone_number(verification.phone_number)
    logging.info("stored_otp: ",stored_otp)

    time.sleep(3)

    if not stored_otp:
        raise HTTPException(status_code=404, detail="OTP not found or phone number is not valid")
    
    if stored_otp[0]['otp_code'] == verification.otp:
        # Successful verification
        return {"status": "Verification successful"}
    raise HTTPException(status_code=400, detail="Invalid OTP")


@api_router.get("/test_api_react_native")
async def test_api_react_native():
    
    time.sleep(5)

    return {"data":"successful"}

@api_router.get("/check_onboarding_status/{email_address}")
async def check_onboarding_status_user(email_address: str):
    logging.info("email address from client: ",email_address)
    
    time.sleep(2)

    user=await check_user_onboarding_status(
        email=email_address
    )

    logging.info("user: ",user)

    result=False if not user else True

    return {"status":result}

@api_router.post("/onboard_user")
async def onboard_new_user(request_body: UserOnboardingRequest):
    logging.info(f"request_body: {request_body}")

    await onboard_new_user_to_db(
        user=request_body
    )

    time.sleep(3)

    return {"message":"successfully onboarded"}

@api_router.post("/user_signup")
async def user_signup(request_body: UserSignUpRequest):
    logging.info("request_body: ",request_body)

    user_by_username=await retrieve_user_by_field_value(
        user=request_body,
        field_name="phone_number",
        field_value=request_body.phonenumber
    )

    time.sleep(4)

    if user_by_username:
        raise HTTPException(
            status_code=403,
            detail=f"User with phonenumber {request_body.phonenumber} already existed"
        )
    

    await insert_new_user(
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

    logging.info("request_body: ",request_body)

    user=await retrieve_user_by_field_value(
        user=request_body,
        field_name="username",
        field_value=request_body.username
    )

    if not user:
        user=await retrieve_user_by_field_value(
            user=request_body,
            field_name="phone_number",
            field_value=request_body.username
        )

        if not user:
            raise HTTPException(
                status_code=403,
                detail=f"Username or phone number does not exist, please try again"
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


