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
    UserSignInRequest,
    UserOnboardingRequest)
from src.database.prompt_template.prompt_template import (
    CREATE_USER_SUMMARY_PROFILE
)
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

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

async def insert_new_user_for_sign_up(user: UserSignUpRequest):
    conn=await get_connection()

    try:
        query = '''
        INSERT INTO users (
            username, 
            phone_number, 
            birthday, 
            password, 
            email, 
            firstname, 
            lastname,
            telegram_handle
        )
        VALUES ($1, $2, $3,$4,$5,$6,$7,$8)
        '''

        hashed_password=hash_password(
            password=user.password
        )
    
        await conn.execute(query, user.username, user.phonenumber, user.birthday, hashed_password,user.email,user.firstname,user.lastname,user.telegram_handle)
        logging.info("Successfuly add user to users table")
    except Exception as e:
        logging.info("Failed to add user to users table, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="server error")

async def update_user_profile_for_onboarding(user: UserOnboardingRequest):
    conn=await get_connection()

    try:
        query = '''
        UPDATE users 
        SET 
            gender = $1,
            gender_preferences = $2,
            age_range = $3,
            height = $4,
            ethnicity = $5,
            children = $6,
            education = $7, 
            job_title =  $8,
            religious_beliefs = $9,
            drink_habit = $10,
            smoke_habit = $11,
            is_onboarding_complete=TRUE
        WHERE username = $12;
        '''
        await conn.execute(query, 
                           user.gender,
                           user.gender_preferences,
                           user.age_range,
                           user.height,
                           user.ethnicity,
                           user.children,
                           user.education,
                           user.job_title,
                           user.religious_beliefs,
                           user.drink_habit,
                           user.smoke_habit,
                           user.username)
        logging.info("Successfuly update user to users table")
    except Exception as e:
        logging.info("Failed to update user information: ",e.args[0])
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
    
async def get_user_phonenumber_by_username(username: str):
    conn=await get_connection()

    try:
        query=f'''
        select 
            u.phone_number
        from users as u
        where u.username=$1;
        '''

        result=await conn.fetch(query,username)

        return result
    except Exception as e:
        print("Failed to retrieve user phone number")
        logging.info(f"Failed to retrieve user ",e.args)
        raise HTTPException(status_code=500,detail="Server error while fetching user phone number")


async def insert_new_pair_to_match_pair_table(
    match_id: str,
    user1: str,
    user2: str
):
    conn=await get_connection()
    
    try:
        query = '''
        INSERT INTO match_pairs (
            match_id, 
            user_1, 
            user_2, 
            user_1_action, 
            user_2_action
        ) 
        VALUES 
            ($1, $2 , $3, NULL, NULL)
        '''

        await conn.execute(query, match_id, user1, user2)
        
        print('Successfuly add pair to match_pairs table')
        logging.info("Successfuly add pair to match_pairs table")
    except Exception as e:
        print("Failed to add pair to match_pairs")
        logging.info("Failed to add pair to match_pairs, error message: ",e.args[0])
        raise HTTPException(status_code=500,detail="Server error while add pairs")
 
async def update_user_status_after_match(
    match_id: str,
    username: str
):
    conn=await get_connection()
    
    try:
        query = '''
        UPDATE users 
        SET 
            status = 'frozen',
            match_reference_id=$1
        WHERE username = $2;
        '''

        await conn.execute(query, match_id,username)
        
        print(f'Successfuly update status for user {username}')
        logging.info(f'Successfuly update status for user {username}')
    except Exception as e:
        print("Failed to update status for user")
        logging.info("Failed to update status for user ",e.args[0])
        raise HTTPException(status_code=500,detail="Server error while updating users")
    
async def insert_notification_for_user(
    username: str,
    category: str,
    message: str
):
    conn=await get_connection()
    
    notification_id = str(uuid.uuid4())
    
    try:
        query = '''
        INSERT INTO notification (
            id,
            receiving_user, 
            category, 
            event_detail
        ) VALUES
        ($1,$2, $3, $4);
        '''

        await conn.execute(query, notification_id, username, category, message)
        
        print(f'Successfuly add notification for user {username}')
        logging.info(f"Successfuly add notification for user {username}")
    except Exception as e:
        print("Fail to add notification for user {username}")
        logging.info("Fail to add notification for user {username}",e.args[0])
        raise HTTPException(status_code=500,detail="Server error while add pairs")
    

async def update_user_is_profile_complete(
    username: str
):
    conn=await get_connection()
    
    try:
        query = '''
        update users 
        set 
            is_profile_creation_complete=TRUE
        where username=$1;
        '''

        await conn.execute(query, username)
        
        print(f'Successfuly update is_profile_creation_complete for user {username}')
        logging.info(f'Successfuly update is_profile_creation_complete for user {username}')
    except Exception as e:
        print("Failed to update is_profile_creation_complete for user")
        logging.info("Failed to update is_profile_creation_complete for user ",e.args[0])
        raise HTTPException(status_code=500,detail="Server error while updating users")
    
async def get_users_action_after_match_and_frozen(username: str):
    conn=await get_connection()

    try:
        query=f'''
        select *
        from users as u, match_pairs as m
        where u.match_reference_id = m.match_id and u.username=$1; 
        '''

        result=await conn.fetch(query,username)
        
        logging.info("get user action successfully")

        return result[0]
    except Exception as e:
        print("Failed to get user action")
        logging.info(f"Failed to retrieve user action",e.args)
        raise HTTPException(status_code=500,detail="Server error while fetching user action")
       
async def get_match_profile_category_and_info(username: str):
    conn=await get_connection()

    try:
        query=f'''
        select *
        from users as u1
        where u1.match_reference_id =(
        select 
            u.match_reference_id
        from users as u
        where u.username=$1) and u1.username != $1;
        '''

        result=await conn.fetch(query,username)
        
        logging.info("get match profile info successfully")

        return result[0] if result else []
    except Exception as e:
        print("Failed to get get match profile ")
        logging.info(f"Failed to rget match profile  ",e.args)
        raise HTTPException(status_code=500,detail="Server error while getting match profile")

async def update_user_action_in_frozen_state(
    username: str,
    user_action_x: str, 
    action: str
):
    conn=await get_connection()
    
    try:
        query = f'''
        update match_pairs 
            set
                {user_action_x}=$1
        where match_id = (
            select 
                u.match_reference_id
            from users as u
            where u.username=$2);
        '''

        await conn.execute(query,action,username)
        
        print(f'Successfuly update action {action} for user {username}')
        logging.info(f'Successfuly update action {action} for user {username}')
    except Exception as e:
        print(f"Failed to update action {action} for user")
        logging.info(f"Failed to update {action} for user ",e.args[0])
        raise HTTPException(status_code=500,detail="Server error while updating users")
    
async def update_all_users_status_to_in_chat_given_match_id(
    match_id: str
):
    conn=await get_connection()
    
    try:
        query = '''
        UPDATE users
        SET 
            status='in_chat'
        WHERE match_reference_id=$1;
        '''

        await conn.execute(query,match_id)
        
        print('Successfuly update status to inchat')
        logging.info('Successfuly update status to inchat')
    except Exception as e:
        print("Failed to update status to inchat")
        logging.info(f"Failed to update user status to inchat ",e.args[0])
        raise HTTPException(status_code=500,detail="Server error while updating users")
    
async def perform_transaction_block_to_handle_reject_event(username: str):
    conn = await get_connection()

    try:
        async with conn.transaction():
            # 1. Delete from match_pairs
            delete_query = '''
                DELETE FROM match_pairs
                WHERE match_id = (
                    SELECT u.match_reference_id
                    FROM users AS u
                    WHERE u.username = $1
                );
            '''
            await conn.execute(delete_query, username)

            # 2. Update users
            update_query = '''
                UPDATE users
                SET 
                    match_reference_id = NULL,
                    status = 'available'
                WHERE match_reference_id = (
                    SELECT match_reference_id
                    FROM users
                    WHERE username = $1
                );
            '''
            await conn.execute(update_query, username)

        logging.info(f"Successfully handled reject event for user '{username}'")

    except Exception as e:
        logging.error(f"Failed to handle reject event for user '{username}': {e}")
        raise HTTPException(status_code=500,detail="Server error while processing reject event")
    
    
async def get_user_notifications(username: str):
    conn = await get_connection()

    try:
        query = '''
        SELECT *
        FROM notification AS n
        WHERE n.receiving_user = $1
        ORDER BY timestamp ASC;
        '''

        result = await conn.fetch(query, username)

        logging.info(f"Fetched user {username} notifications successfully")

        return result
    except Exception as e:
        print(f"Failed to get user {username} notifications")
        logging.error(f"Error while fetching {username} notifications: {e}")
        raise HTTPException(status_code=500, detail="Server error while getting notifications")
    
async def mark_notification_as_seen(notification_id: str):
    conn = await get_connection()
    
    try:
        query = '''
        UPDATE notification
        SET is_seen = TRUE
        WHERE id = $1;
        '''

        await conn.execute(query, notification_id)
        
        print(f'Successfully marked notification {notification_id} as seen')
        logging.info(f'Successfully marked notification {notification_id} as seen')
    except Exception as e:
        print("Failed to update notification status")
        logging.error(f"Failed to update notification status: {e}")
        raise HTTPException(status_code=500,detail="Server error while updating notification")

async def add_unmatch_pair(username1: str, username2: str):
    conn = await get_connection()
    
    try:
        query = '''
        INSERT INTO unmatch_pairs (username1, username2)
        VALUES ($1, $2);
        '''
        await conn.execute(query, username1, username2)
        
        logging.info(f'Successfully added unmatch pair: {username1} and {username2}')
    except Exception as e:
        logging.error(f"Failed to add unmatch pair: {e}")
        raise HTTPException(status_code=500,detail="Server error while adding unmatch pair")
    
# User profile

async def get_saa_convo_user(username: str):
    conn = await get_connection()

    try:
        query = """
        SELECT *
        FROM saachats AS s
        WHERE s.username = $1 AND s.is_post_profile_convo = false
        order by s.timestamp asc;
        """
        result = await conn.fetch(query, username)
        return result

    except Exception as e:
        print("Failed to retrieve Saa conversation")
        logging.info(f"Failed to retrieve Saa conversation: {e}")
        raise RuntimeError("Server error while fetching Saa conversation")

async def update_vector_embedding(username: str, embedding: list[float]):
    conn = await get_connection()
    try:
        vector_str = str(embedding)  # Format: [0.11, 0.42, 0.87, ...]
        query = """
            UPDATE users
            SET embedding = $1::vector
            WHERE username = $2
        """
        await conn.execute(query, vector_str, username)
        
        print("store embeddings sucessfully")
        
    except Exception as e:
        print(f"Failed to update embedding: {e}")
        raise RuntimeError("Can not store embedding to DB")

async def update_user_profile_summary(username: str, summary: str):
    conn = await get_connection()
    try:
        query = """
            UPDATE users
            SET user_profile_summary = $1
            WHERE username = $2
        """
        await conn.execute(query, summary, username)
        print("User profile summary updated successfully.")
    except Exception as e:
        print("Failed to update user profile summary:", e)
        raise RuntimeError("Server error while updating user profile summary")
    
async def update_user_status(username: str, status: str = "available"):
    conn = await get_connection()
    try:
        query = """
            UPDATE users
            SET status = $1
            WHERE username = $2
        """
        await conn.execute(query, status, username)
        print(f"User '{username}' account status set to '{status}'.")
    except Exception as e:
        print("Failed to update user status:", e)
        raise RuntimeError("Server error while updating user status")

async def get_user_record_by_username(username: str):
    conn = await get_connection()
    try:
        query = """
            SELECT *
            FROM users AS u
            WHERE u.username = $1
        """
        result = await conn.fetch(query, username)
        
        return result
    except Exception as e:
        print("Failed to fetch user:", e)
        raise RuntimeError("Server error while fetching user")



def generate_profile_summary(conversation,llm):

    chat_template = PromptTemplate.from_template(CREATE_USER_SUMMARY_PROFILE)

    chain = LLMChain(llm=llm, prompt=chat_template)

    result = chain(
        {
            "conversation": conversation
        },
        return_only_outputs=True
    )
    
    print("result: ",result['text'])
    
    return result['text']


