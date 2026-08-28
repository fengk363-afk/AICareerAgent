"""
Database migration script
Add job lifecycle status fields to jobs table
"""
import asyncio
from sqlalchemy import text
from app.db.database import engine


async def migrate():
    async with engine.begin() as conn:
        # 1. Add status column (default 'active' for existing jobs)
        await conn.execute(
            text("""
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'
            """)
        )
        print('Migration completed: Added status column')

        # 2. Add last_seen_at column
        await conn.execute(
            text("""
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP
            """)
        )
        print('Migration completed: Added last_seen_at column')

        # 3. Add status_changed_at column
        await conn.execute(
            text("""
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMP
            """)
        )
        print('Migration completed: Added status_changed_at column')

        # 4. Add last_synced_at column
        await conn.execute(
            text("""
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP
            """)
        )
        print('Migration completed: Added last_synced_at column')

        # 5. Set last_seen_at = created_at for existing jobs (conservative)
        await conn.execute(
            text("""
                UPDATE jobs
                SET last_seen_at = created_at
                WHERE last_seen_at IS NULL
            """)
        )
        print('Migration completed: Set last_seen_at for existing jobs')

        # 6. Set status_changed_at = created_at for existing ACTIVE jobs
        await conn.execute(
            text("""
                UPDATE jobs
                SET status_changed_at = created_at
                WHERE status_changed_at IS NULL AND status = 'active'
            """)
        )
        print('Migration completed: Set status_changed_at for existing active jobs')

        # 7. Create indexes
        await conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON jobs(status)
            """)
        )
        print('Migration completed: Created idx_jobs_status')

        await conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_at
                ON jobs(last_seen_at)
            """)
        )
        print('Migration completed: Created idx_jobs_last_seen_at')

        # 8. Create unique constraint on (source, source_job_id)
        # Only add if source_job_id is not null (some mock jobs may not have it)
        await conn.execute(
            text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'uq_job_source_source_job_id'
                    ) THEN
                        ALTER TABLE jobs
                        ADD CONSTRAINT uq_job_source_source_job_id
                        UNIQUE (source, source_job_id);
                    END IF;
                END $$
            """)
        )
        print('Migration completed: Added unique constraint on (source, source_job_id)')

        print('All job lifecycle migrations completed successfully')


if __name__ == '__main__':
    asyncio.run(migrate())
