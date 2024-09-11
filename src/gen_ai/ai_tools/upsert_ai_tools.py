from langchain.embeddings import OpenAIEmbeddings
import sys
import os
import asyncpg
import asyncio
import pandas as pd
from pinecone import Pinecone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from src.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_ALL_AI,
    OPENAI_API_KEY
)

pc=Pinecone(api_key=PINECONE_API_KEY)
index=pc.Index(PINECONE_INDEX_ALL_AI)


embeddings_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# // remove all existing data first
index.delete(delete_all=True)

# Read the Excel file
file_path = 'app_config/database_schema.xlsx'
sheet_name = 'ai_tools_compile'

df = pd.read_excel(file_path, sheet_name=sheet_name)

vectors=[{"id":row['tool_name'],
          "values":embeddings_model.embed_query(row['description']),
          "metadata":{
            "tool_url":row['tool_url'],
            "icon_url":row['icon_url'],
            "category":row['category'],
            "description":row['description'],
            "performance":row['performance'],
            "popularity":row['popularity'],
            "security":row['security'],
            "ease_of_use":row['ease_of_use'],
            "api_support":row['api_support'],
          }
          } for _,row in df.iterrows()]

print("vectors: ",vectors)

index.upsert(
    vectors=vectors
)