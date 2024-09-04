import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pinecone
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from pinecone import Pinecone
import random
import itertools
from langchain_community.embeddings import AzureOpenAIEmbeddings
from typing import Optional,Union

from src.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_PDF
)

pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(PINECONE_INDEX_PDF)

def query_by_username_dockey(
        username:str, 
        doc_key: str,
        query: str,
        top_k: int,
        embedding_model: Optional[Union[OpenAIEmbeddings,AzureOpenAIEmbeddings]]=None
):
    embeddings_model = OpenAIEmbeddings() if not embedding_model else embedding_model
    embedding_query=embeddings_model.embed_query(query)
    results=index.query(
    vector=embedding_query,
    filter={
        "username": {"$eq": username},
        "doc_key": doc_key
    },
    top_k=top_k,
    include_metadata=True)

    return results['matches']

    