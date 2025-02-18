DERIVE_GENDER_PREFERENCES_FROM_CONVERSATION = """
Given the following conversation between user and our AI agent for a dating application, determine 4 information: 
1. gender of the user.
2. gender preferences the user is looking for.
3. age of user
4. age range the user of partner the user is looking for

Instructions:
- Based on the conversation, determine what 4 information mentioned above.
- Return in the json format as example below so that i can use json.loads function to parse it:

{desired_format}

For user's gender preferences, 
- If user prefer both genders, return Both.
- If you can not determine the gender preferences from the conversation, please return Null 
- Your response of this field is restricted to only 4 values: Male, Female, Both, Null

For user's gender
- If you can not determine user gender, return Null
- Your response of this field is restricted to only 3 values: Male, Female, Null


----------
CHAT HISTORY: {chat_history}

----------
Your response:
"""