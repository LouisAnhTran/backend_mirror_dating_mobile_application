
from typing import List
import json
import logging
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.embeddings import AzureOpenAIEmbeddings
from langchain_community.chat_models import AzureChatOpenAI
from datetime import datetime

from src.gen_ai.rag_pdf.pinecone_operation import query_by_username_dockey
from src.models.requests import (
    SingleChatMessageRequest
)
from src.database.db_operation.pdf_query_pro.db_operations import (
    insert_entry_to_mesasages_table
)
from src.database.db_operation.sia_profile_creation.db_operations import (
    get_all_categories_by_username,
    insert_entry_to_sia_chats_table,
    get_category_by_username_and_id
)
from src.gen_ai.sia_engine.prompt_template import (
    SAA_GENERATE_QUESTION,
    CONDENSE_HISTORY_TO_STANDALONE_QUERY_TEMPLATE,
    INTENT_DETECTION,
    EXTRACT_SUBTOPICS_AND_TAGS
)
from src.gen_ai.sia_engine.constant import (
    INTENT
)

def format_chat_history(chat_history: List[SingleChatMessageRequest]) -> ChatMessageHistory:
    """Converts chat history from ChatbotSingleMessage to ChatMessageHistory for usage with langchain
    Args:
        chat_history (List[ChatbotSingleMessage]): Previous chat history containing sender and content
    Returns:
        ChatMessageHistory: Formatted chat history compatible with LangChain
    """
    chat_history_formatted = ChatMessageHistory()
    for message in chat_history:
        if message.role == "user":
            chat_history_formatted.add_user_message(message.content)
        elif message.role == "system":
            # revert output format
            chat_history_formatted.add_ai_message(
                message=message.content
            )
        else:
            logging.info("sender of this message is not valid")

    return chat_history_formatted

def generate_standalone_query(
        llm: AzureChatOpenAI,
        user_query: SingleChatMessageRequest,
        history_messages: List[SingleChatMessageRequest]):
    formatted_chat_history=format_chat_history(
        chat_history=history_messages
    )
    logging.info("formatted_chat_history: ",formatted_chat_history)

    question_generator_template = PromptTemplate.from_template(
        CONDENSE_HISTORY_TO_STANDALONE_QUERY_TEMPLATE
    )

    chain = LLMChain(llm=llm, prompt=question_generator_template)

    response=chain(
        {"chat_history": format_chat_history,"user_response":user_query}, return_only_outputs=True
    )

    logging.info("standalone_query: ",response['text'])

    return response['text']

def intent_detection(
    llm: AzureChatOpenAI,
    user_latest_response: str
) -> str:
    logging.info("user query: ",user_latest_response)

    question_generator_template = PromptTemplate.from_template(
        INTENT_DETECTION
    )

    chain = LLMChain(llm=llm, prompt=question_generator_template)

    response=chain(
        {"intent_examples": INTENT,"user_query":user_latest_response}, return_only_outputs=True
    )
    
    logging.info("intent detected: ",response['text'])

    return response['text']

async def generate_system_response(
        llm: AzureChatOpenAI,
        openai_embeddings: AzureOpenAIEmbeddings,
        standalone_query: str,
        username: str,
        history_messages: List[SingleChatMessageRequest]
):
    logging.info("pass this stage 1 ")

    all_categories= await get_all_categories_by_username(
        username=username
    )

    logging.info("all categories: ",all_categories)

    def valid_sub_topics(sub_topics: dict):
        if not sub_topics:
            return False
        
        if len(sub_topics['subtopics'])<2:
            return False
        
        for sub_topic in sub_topics['subtopics']:
            if len(sub_topic['tags'])<2:
                return False
        
        return True
    
    category_to_generate_question_for=None
    sub_topics_for_prompt_templates=None
    for category in all_categories:
        sub_topics=json.loads(category['payload'])
        if not valid_sub_topics(
            sub_topics=sub_topics):
            logging.info("need to generate question for ",category['category_name'])
            category_to_generate_question_for=category
            sub_topics_for_prompt_templates=sub_topics
            break

    desired_format='''
    {"sub_topics":[
        {
            "titles": "watching movies",
            "interest_Score": 9, 
            "tags": ["spider man, marvel, horror movies"],
            "explaination": "user seems to be really into watching movies, specially spider man, marverl and horror movies, indicating he is adventerous,....' 
        },
        {
            "titles": "play sport",
            "interest_Score": 9, 
            "tags": ["football, liverpool, premimier league"],
            "explaination": "user has an absolute passion for football and he has been watching EPL games and he has been Liverpool fan for 10 years, he also spend much time to play football. So he is sporty, caring about this appearance, fitness, loyal,...' 
        }
    ]}
    '''

    formatted_chat_history=format_chat_history(
        chat_history=history_messages
    )

    chat_template = PromptTemplate.from_template(SAA_GENERATE_QUESTION)

    chain = LLMChain(llm=llm, prompt=chat_template)

    response = chain(
        {
            "category": category_to_generate_question_for['category_name'],
            "category_description": category_to_generate_question_for['category_description'],
            "desired_final_format": desired_format,
            "current_information": sub_topics_for_prompt_templates,
            "chat_history": formatted_chat_history,
            "user_latest_response": standalone_query
        },
        return_only_outputs=True
    )

    logging.info("llm question: ",response['text'])


    # // store llm response to db
    await insert_entry_to_sia_chats_table(
        username=username,
        timestamp=datetime.now(),
        role="saa",
        content=response['text']
    )

    return response['text']

async def extract_tag_sub_topics(
    llm: AzureChatOpenAI,
    user_latest_response: str,
    category_id: int,
    user_name: str
) :
    logging.info("user query: ",user_latest_response)

    question_generator_template = PromptTemplate.from_template(
        EXTRACT_SUBTOPICS_AND_TAGS
    )

    example="""
        {
            "subtopics": [
            {
                "title": "Relax",
                "interest_score": 5,
                "tags": ['alone','home','solo'],
                "explaination": "User uses toned language (“most”)"
            },
            {
                "title": "Reading",
                "interest_score": 8,
                "tags": ['non-fiction','sociology','fiction','fantasy','hunger games','foreshadowing'],
                "explaination": "User exhibits a strong degree of interest towards the sub-topic, provides many details, and use strongly toned language"
            },
            ]
        }
    """

    chain = LLMChain(llm=llm, prompt=question_generator_template)

    result=await get_category_by_username_and_id(
        username=user_name,
        category_id=category_id
    )

    logging.info("result: ",result)

    sub_topics=json.loads(result[0]['payload'])

    response=chain(
        {"user_response": user_latest_response,"user_profile":sub_topics,
         "example":example}, return_only_outputs=True
    )
    
    logging.info("entities_extracted: ",response['text'])
