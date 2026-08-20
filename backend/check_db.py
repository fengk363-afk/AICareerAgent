import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import ResumeProfile


async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ResumeProfile)
            .order_by(ResumeProfile.created_at.desc())
        )

        rows = result.scalars().all()

        print("数量:", len(rows))

        for r in rows:
            print("\nID:", r.id)
            print("SKILLS:", r.skills)
            print("EXPERIENCE:", r.experience)
            print("EDUCATION:", r.education)
            print("SUMMARY:", r.summary)


if __name__ == "__main__":
    asyncio.run(test())
