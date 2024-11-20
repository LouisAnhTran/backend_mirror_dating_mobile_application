import asyncpg
import os
from dotenv import load_dotenv

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.database.db_connection.connection import get_connection

LIST_OF_TABLES=['ai_tools_bookmarks','messages','documents','ai_tools','users','mobile_phone_otp_verification']

async def mobile_phone_otp_verification_table(table_name: str):
    conn=await get_connection()

    try:
        await conn.execute(f'''
                DROP TABLE IF EXISTS {table_name} CASCADE;
        ''')
        print(f"droped table {table_name} succesfully")
    except Exception as e:
        print(f"failed to drop {table_name} table ",e)
        return

    try:
        await conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                phone_number VARCHAR(100) NOT NULL UNIQUE,
                otp_code VARCHAR(100) NOT NULL
            );

        ''')
        print(f"created table {table_name} successfully")
    except Exception as e:
        print(f"failed to drop table {table_name} ",e)

async def ai_tools_table():
    conn=await get_connection()

    try:
        await conn.execute('''
                DROP TABLE IF EXISTS ai_tools CASCADE;
        ''')
        print("droped table ai_tools succesfully")
    except Exception as e:
        print("failed to drop ai_tools table ",e)
        return

    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_tools (
                tool_name VARCHAR(100) NOT NULL UNIQUE,
                tool_url VARCHAR(300) NOT NULL,
                icon_url VARCHAR(300) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                performance FLOAT4 NOT NULL,
                popularity FLOAT4 NOT NULL,
                security FLOAT4 NOT NULL,
                ease_of_use FLOAT4 NOT NULL,
                api_support BOOLEAN NOT NULL,
                free BOOLEAN NOT NULL,
                PRIMARY KEY (tool_name)
            );

        ''')
        print("created table ai_tools successfully")
    except Exception as e:
        print("failed to drop table ai_tools ",e)

async def users_table(table_name: str):
    conn=await get_connection()

    try:
        await conn.execute(f'''
                DROP TABLE IF EXISTS {table_name} CASCADE;
        ''')
        print(f"droped table {table_name} succesfully")
    except Exception as e:
        print(f"failed to drop {table_name} table ",e)
        return

    try:
        await conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                username VARCHAR(100) NOT NULL unique,
                phone_number VARCHAR(100) NOT NULL unique,
                birthday VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                firstname VARCHAR(100) NOT NULL,
                lastname VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                PRIMARY KEY (phone_number)
            );

        ''')
        print(f"created {table_name} table successfully")
    except Exception as e:
        print(f"failed to drop table {table_name} ",e)

async def ai_tools_bookmarks_table():
    conn=await get_connection()

    try:
        await conn.execute('''
                DROP TABLE IF EXISTS ai_tools_bookmarks CASCADE;
        ''')
        print("droped table ai_tools_bookmarks succesfully")
    except Exception as e:
        print("failed to drop ai_tools_bookmarks table ",e)
        return

    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_tools_bookmarks (
                tool_name VARCHAR(100) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
	            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                foreign key (email) references users(email)
                    on delete cascade
                    on update cascade,
                foreign key (tool_name) references ai_tools(tool_name)
                    on delete cascade
                    on update cascade,
                PRIMARY KEY (email,tool_name)
            );

        ''')
        print("created table ai_tools_bookmarks successfully")
    except Exception as e:
        print("failed to drop table ai_tools_bookmarks ",e)

async def documents_table():
    conn=await get_connection()

    try:
        await conn.execute('''
            DROP TABLE IF EXISTS documents CASCADE;
        ''')
        print("dropped table documents succesfully")
    except Exception as e:
        print("failed to drop documents table ",e)
        return

    try:
        await conn.execute('''
           CREATE TABLE IF NOT EXISTS documents (
	            s3_dockey varchar(200) NOT NULL,
                doc_name varchar(500) NOT NULL,
	            email VARCHAR(100),
                no_of_pages INT NOT NULL,
                doc_size FLOAT NOT NULL, 
	            uploaded_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	            foreign key (email) references users(email)
                    on delete cascade
                    on update cascade,
	            primary key (s3_dockey)
            );

        ''')
        print("created documents table successfully")
    except Exception as e:
        print("failed to drop table documents ",e)

async def messages_table():
    conn=await get_connection()

    try:
        await conn.execute('''
            DROP TABLE IF EXISTS messages CASCADE;
        ''')
        print("dropped table message succesfully")
    except Exception as e:
        print("failed to drop messages table ",e )
        return
    
    try:
        await conn.execute('''
           CREATE TABLE IF NOT EXISTS messages (
                doc_name varchar(500) NOT NULL,
                email VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
	            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	            foreign key (email) references users(email)
                    on delete cascade
                    on update cascade,
	            primary key (doc_name,email,timestamp)
            );

        ''')
        print("created messages table successfully")
    except Exception as e:
        print("failed to create table documents ",e)


async def drop_any_table(table_name):
    conn=await get_connection()

    try:
        await conn.execute(f'''
            DROP TABLE IF EXISTS {table_name} CASCADE;
        ''')
        print(f"dropped table {table_name} succesfully")
    except Exception as e:
        print(f"failed to drop {table_name} table",e)

async def refresh_all():
    conn=await get_connection()

    try:
        for table in LIST_OF_TABLES:
            await drop_any_table(table)

        await users_table()
        await ai_tools_table()
        await documents_table()
        await messages_table()
        await ai_tools_bookmarks_table()
    except Exception as E:
        print("error when refresh database")

if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv)!=2:
        print("please provide table name")
        sys.exit(1)

    if sys.argv[1] not in LIST_OF_TABLES and sys.argv[1] != "all":
        LIST_OF_TABLES.append("all")
        print(f"please type in one of these table: {','.join(LIST_OF_TABLES)}")
        sys.exit(1)
    
    if sys.argv[1]=="all":
        asyncio.run(refresh_all())

    if sys.argv[1]=="users":
        asyncio.run(users_table(sys.argv[1]))

    if sys.argv[1]=="documents":
        asyncio.run(documents_table())

    if sys.argv[1]=="messages":
        asyncio.run(messages_table())

    if sys.argv[1]=="ai_tools":
        asyncio.run(ai_tools_table())

    if sys.argv[1]=="ai_tools_bookmarks":
        asyncio.run(ai_tools_bookmarks_table())

    if sys.argv[1]=="mobile_phone_otp_verification":
        asyncio.run(mobile_phone_otp_verification_table(sys.argv[1]))

