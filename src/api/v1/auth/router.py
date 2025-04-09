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
import json
from datetime import datetime, date


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
    MatchPairsRequest,
    GenerateUserProfileSummaryTagsRequest,
    GetMatchProfileOverview,
    AcceptMatchRequest,
    RejectMatchRequest,
    GetPotentialMatchUsername,
    GetNotificationRequest,
    MarkNotificationSeenRequest
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
    insert_notification_for_user,
    update_user_is_profile_complete,
    get_users_action_after_match_and_frozen,
    get_match_profile_category_and_info,
    update_user_action_in_frozen_state,
    update_all_users_status_to_in_chat_given_match_id,
    perform_transaction_block_to_handle_reject_event,
    get_user_notifications,
    mark_notification_as_seen,
    generate_profile_summary,
    update_user_profile_summary,
    update_vector_embedding,
    get_saa_convo_user,
    add_unmatch_pair,
    get_user_record_by_username,
    update_user_status
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
    generate_saa_response,
    generate_user_profile_summary_with_tags_saa
)
from src.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AWS_ACCESS_KEY,
    AWS_SECRET_ACCESS_KEY,
    AWS_BUCKET_NAME_DEV,
    AWS_REGION,
    OPENAI_API_KEY,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    AWS_LAMBDA_FUNCTION_NAME,
    AWS_ACCESS_KEY_MIRROR,
    AWS_SECRET_ACCESS_KEY_MIRROR
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
from langchain_openai import ChatOpenAI

api_router = APIRouter()

# Twilio configuration
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# In-memory OTP storage (consider using a database in production)
otp_store = {}

# init s3 client
s3_client = boto3.client('s3', 
                         aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

lambda_client = boto3.client("lambda", aws_access_key_id=AWS_ACCESS_KEY_MIRROR, aws_secret_access_key=AWS_SECRET_ACCESS_KEY_MIRROR, region_name=AWS_REGION) 


# init LLM, I am using gpt-4o for this project
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=OPENAI_API_KEY
)

# init embedding model, I am 'text-embedding-ada-002' model from Open AI
embedding_model=OpenAIEmbeddings(
    model='text-embedding-ada-002',
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
        
        my_action=None
        my_match_action=None
        
        if user[0]['status']=='frozen':
            super_user_data=await get_users_action_after_match_and_frozen(
                username=user[0]['username']
            )
            
            if super_user_data['user_1']==user[0]['username']:
                my_action=super_user_data['user_1_action']
                my_match_action=super_user_data['user_2_action']
            else:
                my_action=super_user_data['user_2_action']
                my_match_action=super_user_data['user_1_action']
            
        
        return {"status": "Verification successful",
                "username": user[0]['username'],
                "is_onboarding_complete": user[0]['is_onboarding_complete'],
                "is_profile_creation_complete": user[0]['is_profile_creation_complete'],
                "user_status": user[0]['status'],
                "my_action": my_action,
                "my_match_action": my_match_action
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

# SAA 

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
    
    # todo
    # update is_profile_complete user
    if saa_response['is_ended']: 
        await update_user_is_profile_complete(username=request.username)    

    return {"response": saa_response['body'],"is_ended":saa_response['is_ended']}

    # return {"response": saa_response['body'],"is_ended":True}


@api_router.post("/generate_user_profile_summary_with_tags")
async def generate_user_profile_summary_with_tags(request: GenerateUserProfileSummaryTagsRequest):
    logging.info("username: ",request.username)
    
    # # trigger finding matching
    # response = lambda_client.invoke(
    #     FunctionName=AWS_LAMBDA_FUNCTION_NAME,
    #     InvocationType='Event',  # ✅ fire-and-forget
    #     Payload=json.dumps({"msg": "hi lambda"})
    # )
    
    # logging.info("response status: ",response['StatusCode'])
        
    # task 2: call saa to popuate ten categories
    # TODO TODO
    await generate_user_profile_summary_with_tags_saa(username=request.username)
    
    # task 3: BE build user profile summary
    logging.info("username: ",request.username)
    
    user_convo=await get_saa_convo_user(username=request.username)
      
    # process user convo
    user_convo_chat=[f"{'chatbot' if entry['role']=='assistant' else 'user'}: {entry['content']}" for entry in user_convo]
    
    print("user convo chat: ",user_convo_chat)
    
    user_profile_summary=generate_profile_summary(
        conversation=user_convo_chat,
        llm=llm
    )
    
    print("user_profile_summary: ",user_profile_summary)
    
    await update_user_profile_summary(username=request.username,
                                      summary=user_profile_summary)
    
    embeddings_of_user_profile=embedding_model.embed_query(user_profile_summary)
    
    print("embeddings_of_user_profile: ",embeddings_of_user_profile)
    
    print("len of embedding ",len(embeddings_of_user_profile))
    
    await update_vector_embedding(username=request.username,
                                  embedding=embeddings_of_user_profile)

    return {"response": "successful"}

@api_router.get("/get_match_profile_summary_with_tags/{username}")
async def read_user(username: str):
    logging.info("username: ",username)
    
    user_match_ecord=await get_match_profile_category_and_info(
        username=username
    )
    
    logging.info("user_match_record: ",user_match_ecord)
    
    if not user_match_ecord:
        raise HTTPException(status_code=403,detail="Can not find profile details for this user")
    
    logging.info("user record: ",user_match_ecord)
    
    user_summary_with_tags=user_match_ecord['user_profile_summary_tags']
    
    logging.info("user_summary_with_tags: ",user_summary_with_tags)
    
    json_formatted_profile=json.loads(user_summary_with_tags)
    
    logging.info("result: ",json_formatted_profile)
    
    return {"response": json_formatted_profile}

@api_router.get("/get_own_user_profile_summary_with_tags/{username}")
async def read_user(username: str):
    logging.info("username: ",username)
    
    user_record=await get_user_record_by_username(
        username=username
    )
    
    if not user_record:
        raise HTTPException(status_code=403,detail="Can not find profile details for this user")
    
    logging.info("user record: ",user_record)
    
    user_summary_with_tags=user_record[0]['user_profile_summary_tags']
    
    logging.info("user_summary_with_tags: ",user_summary_with_tags)
    
    json_formatted_profile=json.loads(user_summary_with_tags)
    
    logging.info("result: ",json_formatted_profile)
    
    return {"response": json_formatted_profile}

@api_router.get("/get_own_user_information/{username}")
async def read_user(username: str):
    logging.info("username: ",username)
    
    user_record=await get_user_record_by_username(
        username=username
    )
    
    if not user_record:
        raise HTTPException(status_code=403,detail="Can not find profile details for this user")
    
    logging.info("user record: ",user_record)
    
    user_record=user_record[0]
    
    return {"response": user_record}


# MATCHING
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
                message=f"Mirror has found user with username {pair[1] if count==0 else pair[0]}, which we think is a perfect match for you"
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


@api_router.post("/get_match_profile_overview")
async def get_match_profile_overview(request: GetMatchProfileOverview):
    logging.info("username: ",request.username)
    
    # for match info request, we must return the match profile categories summary + username
    
    # this function help retrieve the whole record of the matched user to a specific user, for example, given user Louis, i will retrieve his match, Emma
    match_user_record=await get_match_profile_category_and_info(
        username=request.username
    )
    
    logging.info("match_user_record: ",match_user_record)
    
    match_username=match_user_record['username']
    
    return {"match_username": match_username
            #to do return match user summary profile
            }

@api_router.post("/get_match_username")
async def get_username_of_potential_match(request: GetPotentialMatchUsername):
    logging.info("username: ",request.username)
    
    # for match info request, we must return the match profile categories summary + username
    
    # this function help retrieve the whole record of the matched user to a specific user, for example, given user Louis, i will retrieve his match, Emma
    match_user_record=await get_match_profile_category_and_info(
        username=request.username
    )
    
    if not match_user_record:
        raise HTTPException(status_code=404, detail=f"There is no match for user {request.username}")
    
    
    logging.info("match_user_record: ",match_user_record)
    
    match_username=match_user_record['username']
    
    birthday = datetime.strptime(match_user_record['birthday'], "%Y-%m-%d").date()
    today = date.today()
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    
    return {"match_username": match_username,
            "gender": match_user_record['gender'],
            "age": age
            }


@api_router.post("/get_match_telegram_handle")
async def get_match_telegram_handle(request: GetPotentialMatchUsername):
    logging.info("username: ",request.username)
    
    # for match info request, we must return the match profile categories summary + username
    
    # this function help retrieve the whole record of the matched user to a specific user, for example, given user Louis, i will retrieve his match, Emma
    match_user_record=await get_match_profile_category_and_info(
        username=request.username
    )
    
    if not match_user_record:
        raise HTTPException(status_code=404, detail=f"There is no match for user {request.username}")
    
    logging.info("match_user_record: ",match_user_record)
    
    telegram_handle=match_user_record['telegram_handle']
    
    return {"response": telegram_handle
            }
    
    

@api_router.get("/get_notification/{username}")
async def get_username_of_potential_match(username: str):
    logging.info("username: ",username)
    
    user_notifications=await get_user_notifications(
        username=username
    )
        
    return {"data": user_notifications
            }
    
@api_router.post("/mark_notifcation_as_seen")
async def mark_notifcation_as_seen(request: MarkNotificationSeenRequest):
    logging.info("notification id: ",request.notification_id)
    
    await mark_notification_as_seen(notification_id=request.notification_id)
        
    return {"response": "mark notification as seen successfully"
            }


@api_router.post("/accept_match")
async def accept_match_request(request: AcceptMatchRequest):
    logging.info("username of user accept the match: ",request.username)
    
    # accept match logic
    user_and_match_actions=await get_users_action_after_match_and_frozen(
        username=request.username
    )
    
    logging.info("user_and_match_actions: ",user_and_match_actions)
    
    # first need to get match action first
    if user_and_match_actions['user_1']==request.username:
        match_action=user_and_match_actions['user_2_action']
        match_user=user_and_match_actions['user_2']
    else:
        match_action=user_and_match_actions['user_1_action']
        match_user=user_and_match_actions['user_1']
        
    logging.info("match_action: ",match_action)
    logging.info("match_user: ",match_user)

    match_reference_id=user_and_match_actions['match_id']
    # case 1
    # if louis accept match with Emma but Emma has yet to accept yet, we simply update action of Louis and notifiction to Emma
    if not match_action:
        await update_user_action_in_frozen_state(
                username=request.username,
                user_action_x='user_1_action' if request.username==user_and_match_actions['user_1'] else 'user_2_action',
                action='accept'
            )
        
        # add event to notification table
        # TODO
        await insert_notification_for_user(
                username=match_user,
                category="accepted_match",
                message=f"{request.username} has accepted the match, you can also accept to start sending messages or reject"
        )
        
        
        # notify emma
        # send notification if socket connection is live
        if match_user in active_connections:
            await active_connections[match_user].send_json({
                "type": "your_match_accept"
            })
        
        else:
            # Send sms via Twilio
            try:
                client.messages.create(
                    body=f"Hey {match_user}, {request.username} accept the match, please accept to start talking",
                    from_=TWILIO_PHONE_NUMBER,
                    to=await get_user_phonenumber_by_username(
                        username=match_user
                    )
                )
                print(f"send sms to user {match_user} successfully")
            except Exception as e:
                print(f"error when sending sms to {match_user}, error details {e}")
            
    else: # Emma already accept, move both in chat status, update Louis action, and send notification to Louis
        
        # update louis action to accept
        await update_user_action_in_frozen_state(
                username=request.username,
                user_action_x='user_1_action' if request.username==user_and_match_actions['user_1'] else 'user_2_action',
                action='accept'
        )
        
        # move both Louis and Emma to in chat pool
        await update_all_users_status_to_in_chat_given_match_id(
            match_id=match_reference_id
        )
        
        # add event to notification table
        # TODO
        await insert_notification_for_user(
                username=match_user,
                category="accepted_match",
                message=f"{request.username} has also accepted the match, you can start sending mesages to each other"
        )
        
        # send notification to Emma
        # send notification if socket connection is live
        if match_user in active_connections:
            await active_connections[match_user].send_json({
                "type": "your_match_accept"
            })
        
        else:
            # Send sms via Twilio
            try:
                client.messages.create(
                    body=f"Hey {match_user}, {request.username} accept the match, two of you can start talking now, let say hello to {request.username}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=await get_user_phonenumber_by_username(
                        username=match_user
                    )
                )
                print(f"send sms to user {match_user} successfully")
            except Exception as e:
                print(f"error when sending sms to {match_user}, error details {e}")
        
    return {"response": f"Your accept request has been seen to {match_user} successfully"
            }
    
@api_router.post("/reject_match")
async def reject_match_request(request: RejectMatchRequest):
    logging.info("username of user reject the match: ",request.username)
    
    # we need this information to know which user to send notifications
    user_and_match=await get_users_action_after_match_and_frozen(
        username=request.username
    )
    
    user_get_rejected=user_and_match['user_2'] if request.username==user_and_match['user_1'] else user_and_match['user_1']
    
    logging.info("user_get_rejected: ",user_get_rejected)
    
    # implement transaction block to update 
    await perform_transaction_block_to_handle_reject_event(
        username=request.username
    )
    
    # TO DO
    # add unmatched pair to unmatch table to avoid future matching 
    await add_unmatch_pair(username1=request.username,
                           username2=user_get_rejected)
    
    # to do update notification table for both users
    await insert_notification_for_user(
        username=user_get_rejected,
        category="rejected_match",
        message=f"{request.username} has become unavailable, you can no longer chat with this user, Mirror is working hard to find another match for you"
    )
    
    # To do change user status from frozen to availble
    await update_user_status(username=request.username,status='available')
    
    await update_user_status(username=user_get_rejected,status='available')
    
    
    # send notification
    if user_get_rejected in active_connections:
        await active_connections[user_get_rejected].send_json({
                "type": "your_match_reject"
            })
        
    else:
        # Send sms via Twilio
        try:
            client.messages.create(
                body=f"Hey {user_get_rejected}, {request.username} is unavailable, Mirror is using her magic to find another match for you",
                from_=TWILIO_PHONE_NUMBER,
                to=await get_user_phonenumber_by_username(
                    username=user_get_rejected
                )
            )
            print(f"send sms to user {user_get_rejected} successfully")
        except Exception as e:
            print(f"error when sending sms to {user_get_rejected}, error details {e}")
    
        
    return {"response": f"You has rejected the match succesfully"
            }
    