import aiosqlite
import os

DB_PATH = 'data/mirror.db'

async def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')
        
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS message_mapping (
                source_msg_id INTEGER PRIMARY KEY,
                dest_msg_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS processed_messages (
                source_msg_id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def map_message(source_id: int, dest_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO message_mapping (source_msg_id, dest_msg_id) VALUES (?, ?)',
            (source_id, dest_id)
        )
        await db.commit()

async def get_mapped_message(source_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT dest_msg_id FROM message_mapping WHERE source_msg_id = ?', (source_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def is_message_processed(source_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT 1 FROM processed_messages WHERE source_msg_id = ?', (source_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row)

async def mark_message_processed(source_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO processed_messages (source_msg_id) VALUES (?)',
            (source_id,)
        )
        await db.commit()

async def remove_mapping(source_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM message_mapping WHERE source_msg_id = ?', (source_id,))
        await db.commit()
