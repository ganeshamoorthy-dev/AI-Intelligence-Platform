import asyncio
from app.db.session import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE projects SET webhook_secret = NULL"))
        print("Successfully cleared stale tokens from the database!")

if __name__ == "__main__":
    asyncio.run(main())
