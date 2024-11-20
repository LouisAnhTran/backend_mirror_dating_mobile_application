CONDENSE_HISTORY_TO_STANDALONE_QUERY_TEMPLATE = """Given the following conversation and user latest response, determine if the new follow up question has any reference to the following conversation.
If yes, rephrase the follow up question to be a standalone question that captures the relevant information.
Standalone question should be as comprehensive as possible to preserve the context and history. Follow up question contain it, this, or that, try to understand it refers to and put the exact terms in the standalone question
If not, return the original question.
----------
CHAT HISTORY: {chat_history}
----------
FOLLOWUP QUESTION: {question}
----------
Standalone question:"""


CONVERSATION_WITH_REFERENCES_TEMPLATE = """
You are a friendly expert to answer questions based on the provided context and references. 
 
Instructions:
1. Use clear and detailed language.
2. Present answer clearly and concisely, and keep it short, using Markdown formatting to enhance readability with headings, list items, paraphragh. Apply headings, lists, and appropriate line spacing where necessary.
3. If you don't know the answer, do not make up a solution, say you don't know.

----------
Context from different sources that could be used to help answer the question:
{context}

----------
Chat History:
{chat_history}

----------
Question:
{question}

----------
Response (in correct formatting):
"""