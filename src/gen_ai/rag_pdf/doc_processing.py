
import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pinecone
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from pinecone import Pinecone
import random
import itertools
import logging

load_dotenv()

file_path = r'D:\SUTD_Official\new_drive_location\Solo_Projects\smart_doc_gen_ai\backend\files\test.pdf'


def extract_text_from_pdf(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text,chunk_size=512,chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks_doc = splitter.split_text(text)
    return chunks_doc

def chunks(iterable, batch_size=100):
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))

def create_iterable_vectors(username,doc_key,file_bytes):
    text=extract_text_from_pdf(file_bytes)
    embeddings_model = OpenAIEmbeddings()
    chunk_docs=chunk_text(text)
    vectors=[embeddings_model.embed_query(chunk) for chunk in chunk_docs]
    iterable_vector=[{"id":f"{doc_key}_{i}","values":item[1],"metadata":{"username":username,"doc_key":doc_key,"text":item[0]}} for i,item in enumerate(list(zip(chunk_docs,vectors)))]
    return iterable_vector

def init_pinecone_and_doc_indexing(username,doc_key,file_bytes):
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    with pc.Index(os.getenv("PINECONE_INDEX"), pool_threads=30) as index:
        iterable_vector=create_iterable_vectors(username,doc_key,file_bytes)
        # Send requests in parallel
        async_results = [
            index.upsert(vectors=ids_vectors_chunk, async_req=True)
            for ids_vectors_chunk in chunks(iterable_vector, batch_size=100)
        ]
    # Wait for and retrieve responses (this raises in case of error)
        [async_result.get() for async_result in async_results]
    
    logging.info("index stats: ",index.describe_index_stats())
    
