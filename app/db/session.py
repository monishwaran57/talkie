# app/db/session.py
import psycopg
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from app.core.config import settings

@asynccontextmanager
async def get_db():
    conn = await psycopg.AsyncConnection.connect(
        f"dbname={settings.SQL_DB_NAME} user={settings.SQL_DB_USER} password='{settings.SQL_DB_PASSWORD}' host=localhost port=5432"
    )

    # Set the row factory for the connection
    conn.row_factory = dict_row

    try:
        async with conn.cursor() as cur:
            yield cur
            await conn.commit()
    except Exception:
        await conn.rollback()
        raise
    finally:
        await conn.close()
