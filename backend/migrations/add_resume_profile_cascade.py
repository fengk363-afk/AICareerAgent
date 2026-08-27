"""
Database migration script
Add ON DELETE CASCADE to all foreign keys referencing resume_profiles.id
"""
import asyncio
from sqlalchemy import text
from app.db.database import engine


async def migrate():
    async with engine.begin() as conn:
        # resume_versions
        await conn.execute(
            text("""
                ALTER TABLE resume_versions
                DROP CONSTRAINT IF EXISTS resume_versions_resume_profile_id_fkey,
                ADD CONSTRAINT resume_versions_resume_profile_id_fkey
                FOREIGN KEY (resume_profile_id) REFERENCES resume_profiles(id) ON DELETE CASCADE
            """)
        )
        print('Migration completed: resume_versions -> ON DELETE CASCADE')

        # recommendation_records
        await conn.execute(
            text("""
                ALTER TABLE recommendation_records
                DROP CONSTRAINT IF EXISTS recommendation_records_profile_id_fkey,
                ADD CONSTRAINT recommendation_records_profile_id_fkey
                FOREIGN KEY (profile_id) REFERENCES resume_profiles(id) ON DELETE CASCADE
            """)
        )
        print('Migration completed: recommendation_records -> ON DELETE CASCADE')

        # ai_analysis_records
        await conn.execute(
            text("""
                ALTER TABLE ai_analysis_records
                DROP CONSTRAINT IF EXISTS ai_analysis_records_profile_id_fkey,
                ADD CONSTRAINT ai_analysis_records_profile_id_fkey
                FOREIGN KEY (profile_id) REFERENCES resume_profiles(id) ON DELETE CASCADE
            """)
        )
        print('Migration completed: ai_analysis_records -> ON DELETE CASCADE')

        # job_rankings
        await conn.execute(
            text("""
                ALTER TABLE job_rankings
                DROP CONSTRAINT IF EXISTS job_rankings_profile_id_fkey,
                ADD CONSTRAINT job_rankings_profile_id_fkey
                FOREIGN KEY (profile_id) REFERENCES resume_profiles(id) ON DELETE CASCADE
            """)
        )
        print('Migration completed: job_rankings -> ON DELETE CASCADE')

        # learning_plans
        await conn.execute(
            text("""
                ALTER TABLE learning_plans
                DROP CONSTRAINT IF EXISTS learning_plans_profile_id_fkey,
                ADD CONSTRAINT learning_plans_profile_id_fkey
                FOREIGN KEY (profile_id) REFERENCES resume_profiles(id) ON DELETE CASCADE
            """)
        )
        print('Migration completed: learning_plans -> ON DELETE CASCADE')

        # applications (nullable FK, also safe for CASCADE since deleting a profile
        # means the application's resume reference is no longer valid)
        await conn.execute(
            text("""
                ALTER TABLE applications
                DROP CONSTRAINT IF EXISTS applications_resume_profile_id_fkey,
                ADD CONSTRAINT applications_resume_profile_id_fkey
                FOREIGN KEY (resume_profile_id) REFERENCES resume_profiles(id) ON DELETE CASCADE
            """)
        )
        print('Migration completed: applications -> ON DELETE CASCADE')

        print('All resume_profiles FK constraints updated with ON DELETE CASCADE')


if __name__ == '__main__':
    asyncio.run(migrate())
