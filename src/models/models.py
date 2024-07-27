
from pydantic import BaseModel
import asyncpg
from sql_app.database import get_connection

class Item(BaseModel):
    id: int = None
    name: str
    description: str = None

async def create_item(item: Item):
    conn = await get_connection()
    query = "INSERT INTO items (name, description) VALUES ($1, $2) RETURNING id"
    item_id = await conn.fetchval(query, item.name, item.description)
    await conn.close()
    item.id = item_id
    return item

async def get_item(item_id: int):
    conn = await get_connection()
    query = "SELECT id, name, description FROM items WHERE id = $1"
    row = await conn.fetchrow(query, item_id)
    await conn.close()
    if row:
        return Item(id=row['id'], name=row['name'], description=row['description'])
    return None

async def update_item(item_id: int, item: Item):
    conn = await get_connection()
    query = "UPDATE items SET name = $1, description = $2 WHERE id = $3"
    await conn.execute(query, item.name, item.description, item_id)
    await conn.close()
    item.id = item_id
    return item

async def delete_item(item_id: int):
    conn = await get_connection()
    query = "DELETE FROM items WHERE id = $1"
    await conn.execute(query, item_id)
    await conn.close()
    return True
