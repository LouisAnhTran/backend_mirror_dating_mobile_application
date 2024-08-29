import asyncpg
import os
from dotenv import load_dotenv

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# from src.config import DATABASE_URL
from src.database.connection import get_connection

LIST_OF_TABLES=['users','documents','messages',"all"]

DATABASE_URL='postgresql://postgres:Capstone782425@all-ai-capstone-dev-test-db.c9iqe8mic0wy.ap-southeast-1.rds.amazonaws.com:5432/all_ai_capstone_dev_test_database'

async def users_table():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
                DROP TABLE IF EXISTS users;
        ''')
        print("droped table users succesfully")
    except Exception as e:
        print("failed to drop users table")
        return

    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                PRIMARY KEY (username)
            );

        ''')
        print("created users table successfully")
    except Exception as e:
        print("failed to drop table users")

async def drop_any_table(table_name):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(f'''
            DROP TABLE IF EXISTS {table_name};
        ''')
        print(f"dropped table {table_name} succesfully")
    except Exception as e:
        print(f"failed to drop {table_name} table")
        
async def documents_table():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            DROP TABLE IF EXISTS documents;
        ''')
        print("dropped table documents succesfully")
    except Exception as e:
        print("failed to drop documents table")
        return

    try:
        await conn.execute('''
           CREATE TABLE IF NOT EXISTS documents (
	            s3_dockey varchar(200) NOT NULL,
                doc_name varchar(500) NOT NULL,
	            username VARCHAR(100),
                no_of_pages INT NOT NULL,
                doc_size FLOAT NOT NULL, 
	            uploaded_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	            foreign key (username) references users(username),
	            primary key (s3_dockey)
            );

        ''')
        print("created documents table successfully")
    except Exception as e:
        print("failed to drop table documents")

async def messages_table():
    conn=await get_connection()

    try:
        await conn.execute('''
            DROP TABLE IF EXISTS messages;
        ''')
        print("dropped table message succesfully")
    except Exception as e:
        print("failed to drop messages table")
        return
    
    try:
        await conn.execute('''
           CREATE TABLE IF NOT EXISTS messages (
                doc_name varchar(500) NOT NULL,
                username VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
	            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	            foreign key (username) references users(username),
	            primary key (doc_name,username,timestamp)
            );

        ''')
        print("created messages table successfully")
    except Exception as e:
        print("failed to create table documents")


async def refresh_all():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await drop_any_table("documents")
        await drop_any_table("users")
        await drop_any_table("messages")
        await users_table()
        await documents_table()
        await messages_table()
    except Exception as E:
        print("error when refresh database")

if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv)!=2:
        print("please provide table name")
        sys.exit(1)

    if sys.argv[1] not in LIST_OF_TABLES:
        print(f"please type in one of these table: {LIST_OF_TABLES}")
        sys.exit(1)
    
    if sys.argv[1]=="all":
        asyncio.run(refresh_all())

    if sys.argv[1]=="users":
        asyncio.run(users_table())

    if sys.argv[1]=="documents":
        asyncio.run(documents_table())

    if sys.argv[1]=="messages":
        asyncio.run(messages_table())

