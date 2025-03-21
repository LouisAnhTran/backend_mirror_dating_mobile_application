from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List,Dict
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
import uuid


from src.models.requests import (
    UserSignUpRequest,
    UserSignInRequest,
    ChatMessagesRequest,
    OTPRequest,
    OTPVerification,
    SignInByEmail,
    GetSaaFollowUpOrIntroRequest,
    GetSaaResponseRequest,
    UserOnboardingRequest,
    MatchPairsRequest
    )
from src.utils.user_authentication import create_access_token
from src.database.db_operation.pdf_query_pro.db_operations import (
    insert_entry_to_mesasages_table,
    fetch_all_messages
)
from src.database.db_operation.user_auth.db_operations import (
    add_mobile_phone_and_otp,
    retrieve_otp_by_phone_number,
    insert_new_user_for_sign_up,
    retrieve_user_by_field_value,
    retrieve_saa_history_chat,
    retrieve_user_by_phoneumber,
    update_user_profile_for_onboarding,
    insert_new_pair_to_match_pair_table,
    update_user_status_after_match,
    get_user_phonenumber_by_username,
    insert_notification_for_user
)
from src.utils.user_authentication import (
    hash_password,
    verify_password,
    get_access_token_cookie,
    decode_access_token
    )
from src.gen_ai.sia_engine.chat_processing import (
    generate_saa_follow_up_question,
    generate_saa_intro,
    generate_saa_response
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


# Store WebSocket connections keyed by user_id
active_connections: Dict[str, WebSocket] = {}

@api_router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    
    active_connections[username] = websocket
    
    try:
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        del active_connections[username]
        
# ap endpoints
@api_router.get("/test_ws/{username}")
async def test_ws(username: str):
    if username in active_connections: 
        
        await active_connections[username].send_json({
            "type": "match_accept",
            "from": "server"
        })
        
        return {"status": "websocket_sent"}


@api_router.post("/generate-otp")
async def generate_otp(request: OTPRequest):
    # Generate a random 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # check if this phone number has been used to sign up before
    user=await retrieve_user_by_phoneumber(
        phonenumber=request.phone_number
    )
    
    if user:
        raise HTTPException(
            status_code=403, 
            detail="This phonenumber has been registered, please sign in or use another phone number"
        )
    
    # Store OTP in memory with the associated phone number (use a database for production)
    await add_mobile_phone_and_otp(request.phone_number,otp)

    logger.info("otp: ",request.phone_number)
    
    # Send OTP via Twilio
    try:
        client.messages.create(
            body=f"Your verification code is {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=request.phone_number
        )
        return {"status": "OTP sent successfully"}
    except Exception as e:
        print(f"Twilio error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP") from e


@api_router.post("/verify-otp")
async def verify_otp(verification: OTPVerification):
    stored_otp = await retrieve_otp_by_phone_number(verification.phone_number)
    logging.info("stored_otp: ",stored_otp)
    
    if not stored_otp:
        raise HTTPException(status_code=404, detail="OTP not found or phone number is not valid")
    
    if stored_otp[0]['otp_code'] == verification.otp:
      
        return {"status": "Verification successful"}
        
    raise HTTPException(status_code=400, detail="Invalid OTP")

@api_router.post("/verify-otp-sign-in")
async def verify_otp_signing_in(verification: OTPVerification):
    stored_otp = await retrieve_otp_by_phone_number(verification.phone_number)
    logging.info("stored_otp: ",stored_otp)
    
    if not stored_otp:
        raise HTTPException(status_code=404, detail="OTP not found or phone number is not valid")
    
    if stored_otp[0]['otp_code'] == verification.otp:
        # Successful verification
        user=await retrieve_user_by_phoneumber(
            phonenumber=verification.phone_number
        )
        
        return {"status": "Verification successful",
                "username": user[0]['username'],
                "is_onboarding_complete": user[0]['is_onboarding_complete'],
                "is_profile_creation_complete": user[0]['is_profile_creation_complete']
                }
        
    raise HTTPException(status_code=400, detail="Invalid OTP")

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

@api_router.post("/user_signup")
async def user_signup(request_body: UserSignUpRequest):
    logging.info("request_body: ",request_body)

    await insert_new_user_for_sign_up(
        user=request_body
    )
    
    return {"message": "User registered successfully"}

@api_router.post("/update_user_profile_onboarding")
async def update_user_profile_onboarding(request_body: UserOnboardingRequest):
    logging.info("request_body: ",request_body)

    await update_user_profile_for_onboarding(
        user=request_body
    )
    
    return {"message": "User onboarded successfully"}

@api_router.get("/load_saa_conversation/{username}")
async def load_conversation_saa_user_profile_creation(username: str):
    logging.info("username: ",username)

    # check if prior conversation exists
    history_messages=await retrieve_saa_history_chat(
        username=username
    )

    logging.info("history_message ",history_messages)

    # return a list of all messages to
    return {"response":history_messages}

@api_router.post("/get_saa_intro_or_follow_up")
async def get_saa_intro_or_follow_up(request: GetSaaFollowUpOrIntroRequest):
    logging.info("username: ",request.username)

    # check if prior conversation exists
    history_messages=await retrieve_saa_history_chat(
        username=request.username
    )

    logging.info("history_message ",history_messages)

    if len(history_messages):
        saa_follow_up= await generate_saa_follow_up_question(
            username=request.username
        )
        return {"response": saa_follow_up['body']}
        
    saa_intro=await generate_saa_intro(
        username=request.username
    )

    return {"response":saa_intro['body']}

@api_router.post("/get_saa_response")
async def get_saa_request_given_user_query(request: GetSaaResponseRequest):
    logging.info("username: ",request.username)
    logging.info("user query: ",request.userinput)

    saa_response=await generate_saa_response(
        username=request.username,
        userquery=request.userinput
    )

    return {"response": saa_response['body'],"is_ended":saa_response['is_ended']}


@api_router.post("/match_pairs")
async def upsert_match_pairs(request: MatchPairsRequest):
    logging.info("match_pairs_request: ",request.match_pairs)
    
    match_pairs=[tuple(pair.split("-")) for pair in request.match_pairs]
    
    logging.info("matched_pairs: ",match_pairs)
    
    count=0
    
    # insert new pairs to table match pairs
    for pair in match_pairs:
        # Generate a random UUID (Version 4)
        match_id = str(uuid.uuid4())
        
        await insert_new_pair_to_match_pair_table(
            match_id=match_id,
            user1=pair[0],
            user2=pair[1]
        )
        
        
        for user in pair:
            # update users table status
            await update_user_status_after_match(
                match_id=match_id,
                username=user
            )
            
            # update notification table
            # todo 
            await insert_notification_for_user(
                username=user,
                category="match_found",
                message=f"We found user {pair[1] if count==0 else pair[0]}, a perfect match for you"
            )
            
            count+=1
            
            # send notification if socket connection is live
            if user in active_connections:
                await active_connections[user].send_json({
                    "type": "match_found"
                })
            
            else:
                # Send sms via Twilio
                try:
                    client.messages.create(
                        body=f"Hey {user}, Mirror found a perfect match for you, please check it out",
                        from_=TWILIO_PHONE_NUMBER,
                        to=await get_user_phonenumber_by_username(
                            username=user
                        )
                    )
                    print(f"send sms to user {user} successfully")
                except Exception as e:
                    print(f"error when sending sms to {user}, error details {e}")

    return {"response": "success"}