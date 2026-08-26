"""
Database migration script
Add file_path column to resume_profiles table
"""
import asyncio
from sqlalchemy import text
from app.db.database import engine


async def migrate():
    async with engine.begin() as conn:
        await conn.execute(
            text('ALTER TABLE resume_profiles ADD COLUMN IF NOT EXISTS file_path TEXT')
        )
        print('Migration completed: Added file_path column to resume_profiles')


if __name__ == '__main__':
    asyncio.run(migrate())
