import asyncio
from app.db.session import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE review_runs ADD COLUMN blast_radius_summary TEXT;"))
            print("Successfully added blast_radius_summary to review_runs.")
        except Exception as e:
            print("Error adding blast_radius_summary:", e)
            
        try:
            await conn.execute(text("ALTER TABLE review_runs ADD COLUMN impact_graph_data JSON;"))
            print("Successfully added impact_graph_data to review_runs.")
        except Exception as e:
            print("Error adding impact_graph_data:", e)

if __name__ == "__main__":
    asyncio.run(main())
