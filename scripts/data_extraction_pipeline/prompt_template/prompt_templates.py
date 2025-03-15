DERIVE_GENDER_PREFERENCES_FROM_CONVERSATION = """
Given the following conversation between user and our AI agent for a dating application, determine 4 information: 
1. gender of the user.
2. gender preferences the user is looking for.
3. age of user
4. age range the user of partner the user is looking for
5. Whether the user is trolling the Chat bot 


Instructions:
- Based on the conversation, determine what 4 information mentioned above.
- Return in the json format as example below so that i can use json.loads function to parse it:

{desired_format}

For user's gender preferences, 
- If user prefer both genders, return Both.
- If you can not determine the gender preferences from the conversation, please return Null 
- Your response of this field is restricted to only 4 values: Male, Female, Both, Null

For trolling:
- Your response of this field is restricted to only 3 values: true, false

For user's gender
- If you can not determine user gender, return Null
- If user answer is Other, your response should be Other
- Your response of this field is restricted to only 3 values: Male, Female, Null, Other

For justification_trolling:
- Give your response why this user might be trolling the AI Chat bot.

----------
CHAT HISTORY: 
{chat_history}

----------
Your response:
"""

TEST="""
For trolling:
- Your response of this field is restricted to only 3 values: True, False

For justification_trolling:
- Give your response why this user might be trolling the AI Chat bot.

5. Whether the user is trolling the Chat bot 
"""


MATCHING_TEMPLATE="""
You are an expert in match maker, given the two user conversation history with our dating application, your task is to determine if they are compatible and give your reasons for that

Instructions:
1. Give a clear and comprehensive answer
2. Provide reasons why you think they are a good match

-------------
USER 1 CHAT HISTORY
{user1_chat}

-------------
USER 1 CHAT HISTORY
{user2_chat}


-------------
Your response

"""

CREATE_USER_SUMMARY_PROFILE="""
You are an expert in creating a summary of user profile in the dating application based on the conversation between user and the application AI agent.

Instructions:
1. Provide the detailed summary of user profile based on the conversation
2. Retain all the key and important information. 

-------------
CHAT CONVERSATION
{conversation}

-------------
Your response

"""
