
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
from src.gen_ai.rag_pdf.prompt_template import (
    CONDENSE_HISTORY_TO_STANDALONE_QUERY_TEMPLATE,
    CONVERSATION_WITH_REFERENCES_TEMPLATE
)
from src.models.requests import (
    SingleChatMessageRequest
)
from database.db_operation.pdf_query_pro.db_operations import (
    insert_entry_to_mesasages_table
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
        {"chat_history": format_chat_history,"question":user_query}, return_only_outputs=True
    )

    logging.info("standalone_query: ",response['text'])

    return response['text']


async def generate_system_response(
        llm: AzureChatOpenAI,
        openai_embeddings: AzureOpenAIEmbeddings,
        standalone_query: str,
        username: str,
        history_messages: List[SingleChatMessageRequest],
        doc_key: str,
        top_k: int,
        doc_name: str,
):
    similar_results=query_by_username_dockey(
        username=username,
        doc_key=doc_key,
        query=standalone_query,
        top_k=5,
        embedding_model=openai_embeddings
    )

    logging.info("similar_results: ",similar_results)

    all_texts=[chunk['metadata']['text'] for chunk in similar_results]

    logging.info("all_texts: ",all_texts)

    formatted_chat_history=format_chat_history(
        chat_history=history_messages
    )

    chat_template = PromptTemplate.from_template(CONVERSATION_WITH_REFERENCES_TEMPLATE)

    chain = chat_template | llm

    result = chain.stream(
        {
            "context": all_texts,
            "chat_history": formatted_chat_history,
            "question": standalone_query,
        }
    )

    final_response=""
    for chunk in result:
        final_response+=chunk.content
        yield json.dumps({"intermediate_token":chunk.content}) + "\n"

    yield json.dumps({"last_token": final_response}) + "\n"

    logging.info("test_date_time: ",datetime.now())

    await insert_entry_to_mesasages_table(
        username=username,
        message=final_response,
        docname=doc_name,
        role="system",
        timestamp=datetime.now()
    )