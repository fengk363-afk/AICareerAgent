"""
Database migration script
V7.1: Add job normalized fields for deduplication
"""
import asyncio
import sys
import os
# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from app.db.database import engine


async def migrate():
    async with engine.begin() as conn:
        # 1. Add normalized columns
        await conn.execute(text("""
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS normalized_company VARCHAR(200)
        """))
        print('Migration completed: Added normalized_company column')

        await conn.execute(text("""
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS normalized_title VARCHAR(200)
        """))
        print('Migration completed: Added normalized_title column')

        await conn.execute(text("""
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS normalized_location VARCHAR(200)
        """))
        print('Migration completed: Added normalized_location column')

        # 2. Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_jobs_normalized_company
            ON jobs(normalized_company)
            WHERE normalized_company IS NOT NULL
        """))
        print('Migration completed: Created idx_jobs_normalized_company')

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_jobs_normalized_title
            ON jobs(normalized_title)
            WHERE normalized_title IS NOT NULL
        """))
        print('Migration completed: Created idx_jobs_normalized_title')

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_jobs_normalized_location
            ON jobs(normalized_location)
            WHERE normalized_location IS NOT NULL
        """))
        print('Migration completed: Created idx_jobs_normalized_location')

        # 3. Create composite index for dedup candidate lookup
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_jobs_normalized_dedup
            ON jobs(normalized_company, normalized_title, normalized_location)
            WHERE normalized_company IS NOT NULL
              AND normalized_title IS NOT NULL
        """))
        print('Migration completed: Created idx_jobs_normalized_dedup')

        # 4. Backfill normalized fields for existing jobs
        # We'll use Python to process each job
        result = await conn.execute(text("SELECT id, company, title, location FROM jobs"))
        rows = result.fetchall()
        print(f'Found {len(rows)} jobs to backfill')

        updated = 0
        skipped = 0
        for row in rows:
            job_id, company, title, location = row
            try:
                # Import here to avoid circular imports
                from app.agents.job_source_engine import (
                    normalize_company,
                    normalize_title,
                    normalize_location,
                )
                norm_company = normalize_company(company) if company else None
                norm_title = normalize_title(title) if title else None
                norm_location = normalize_location(location) if location else None

                if norm_company or norm_title or norm_location:
                    await conn.execute(text("""
                        UPDATE jobs
                        SET normalized_company = :norm_company,
                            normalized_title = :norm_title,
                            normalized_location = :norm_location
                        WHERE id = :job_id
                    """), {
                        'norm_company': norm_company,
                        'norm_title': norm_title,
                        'norm_location': norm_location,
                        'job_id': job_id,
                    })
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f'Error backfilling job {job_id}: {e}')
                skipped += 1

        print(f'Backfill completed: updated={updated}, skipped={skipped}')

        # 5. Report statistics
        result = await conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(normalized_company) as with_company,
                COUNT(normalized_title) as with_title,
                COUNT(normalized_location) as with_location
            FROM jobs
        """))
        stats = result.fetchone()
        print(f'Stats: total={stats[0]}, with_company={stats[1]}, with_title={stats[2]}, with_location={stats[3]}')

        print('All V7.1 migrations completed successfully')


if __name__ == '__main__':
    asyncio.run(migrate())
