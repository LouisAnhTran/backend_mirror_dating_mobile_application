from dotenv import load_dotenv
import os
load_dotenv()


def test_env_exists():
    database_url=os.getenv('DATABASE_URL')

    print("database_url: ",database_url)

    assert database_url != None
    assert "postgresql" in database_url