from dotenv import load_dotenv
import os
load_dotenv()


def test_env_exists():
    database_url=os.getenv('DATABASE_URL')
    pinecone_index=os.getenv("PINECONE_INDEX")

    print("database_url: ",database_url)
    print("pinecone_index: ",pinecone_index)

    assert database_url != None
    assert "postgresql" in database_url
    assert "pdf" in pinecone_index