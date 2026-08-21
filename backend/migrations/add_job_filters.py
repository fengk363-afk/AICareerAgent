"""
Database migration script
Add industry and job_category columns to jobs table
"""
import asyncio
from sqlalchemy import text
from app.db.database import engine


async def migrate():
    async with engine.begin() as conn:
        # Add industry column
        await conn.execute(text('ALTER TABLE jobs ADD COLUMN IF NOT EXISTS industry VARCHAR(100)'))
        # Add job_category column
        await conn.execute(text('ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_category VARCHAR(100)'))
        print('Migration completed: Added industry and job_category columns')


if __name__ == '__main__':
    asyncio.run(migrate())
