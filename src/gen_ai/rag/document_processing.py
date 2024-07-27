
import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pinecone
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from pinecone import Pinecone
import random
import itertools

load_dotenv()

file_path = r'D:\SUTD_Official\new_drive_location\Solo_Projects\smart_doc_gen_ai\backend\files\test.pdf'


def extract_text_from_pdf(file_content):
    text = ""
    for page in file_content:
        text += page.get_text()
    return text


if os.path.exists(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    # print(text)
else:
    print(f"The file does not exist at the path: {file_path}")

splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
chunks_doc = splitter.split_text(text)

print("chunks: ",len(chunks_doc))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))
print(index.describe_index_stats())


# Initialize OpenAI Embeddings
embeddings_model = OpenAIEmbeddings()

index.delete(delete_all=True)


# results=index.query(
#     vector=embeddings_model.embed_query("test"),
#     filter={
#         "username": {"$eq": "louis"},
#         "doc_key": "aws"
#     },
#     top_k=1,
#     include_metadata=True
# )

# print(results)

# def chunks(iterable, batch_size=100):
#     """A helper function to break an iterable into chunks of size batch_size."""
#     it = iter(iterable)
#     chunk = tuple(itertools.islice(it, batch_size))
#     while chunk:
#         yield chunk
#         chunk = tuple(itertools.islice(it, batch_size))

# vector_dim = 512
# vectors=[embeddings_model.embed_query(chunk) for chunk in chunks_doc]
# iterable_vector=[{"id":f"louis_anh_tran_aws_{i}","values":vector,"metadata":{"username":"louis_anh_tran","doc_key":"aws"}} for i,vector in enumerate(vectors)]

# print("vectors: ",iterable_vector)
# # example_data_generator = list(map(lambda i: (f'id-{i}', [random.random() for _ in range(vector_dim)]), range(vector_count)))


# # print("example_data_generator: ",example_data_generator)
# # Upsert data with 100 vectors per upsert request asynchronously
# # - Pass async_req=True to index.upsert()

# with pc.Index(os.getenv("PINECONE_INDEX"), pool_threads=30) as index:
#     # Send requests in parallel
#     async_results = [
#         index.upsert(vectors=ids_vectors_chunk, async_req=True)
#         for ids_vectors_chunk in chunks(iterable_vector, batch_size=100)
#     ]
#     # Wait for and retrieve responses (this raises in case of error)
#     [async_result.get() for async_result in async_results]