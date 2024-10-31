import sys
import os
import asyncpg
import asyncio
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from src.database.db_connection.connection import get_connection
from src.config import DATABASE_URL

# Read the Excel file
file_path = 'app_config/database_schema.xlsx'
sheet_name = 'ai_tools_compile'

df = pd.read_excel(file_path, sheet_name=sheet_name)

async def insert_data():

    # Create a connection pool
    conn= await asyncpg.connect(DATABASE_URL)

    # Iterate through the DataFrame and insert each row
    for _, row in df.iterrows():
        try:
            await conn.execute("""
                INSERT INTO ai_tools (tool_name, tool_url, icon_url, category, description, performance, popularity, security, ease_of_use, api_support,free)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,$11)
                ON CONFLICT (tool_name) DO UPDATE
                SET tool_url = EXCLUDED.tool_url,
                    icon_url = EXCLUDED.icon_url,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    performance = EXCLUDED.performance,
                    popularity = EXCLUDED.popularity,
                    security = EXCLUDED.security,
                    ease_of_use = EXCLUDED.ease_of_use,
                    api_support = EXCLUDED.api_support,
                    free = EXCLUDED.free
            """, 
            row['tool_name'], row['tool_url'], row['icon_url'], row['category'], row['description'], 
            row['performance'], row['popularity'], row['security'], row['ease_of_use'], True if int(row['api_support'])==1 else False,True if int(row['free'])==1 else False)
            print(f"Insert succesfully for: {row['tool_name']}")
        except Exception as e:
            print(f"Error inserting {row['tool_name']}: {e}")

# Run the async function
asyncio.run(insert_data())