# app/db/session.py
import psycopg
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from app.core.config import settings

@asynccontextmanager
async def get_db():
    conn = await psycopg.AsyncConnection.connect(
        "dbname=moni user=plank password='Plank@123' host=localhost port=5432"
    )

    try:
        async with conn.cursor() as cur:
            yield cur
            await conn.commit()
    except Exception:
        await conn.rollback()
        raise
    finally:
        await conn.close()
