import asyncpg
import os

_pool: asyncpg.Pool | None = None


async def init_db():
    global _pool

    if _pool:
        return

    _pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        min_size=1,
        max_size=10
    )


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if not _pool:
        raise RuntimeError("Database not initialized")
    return _pool


# ===== helper functions =====

async def fetch(query: str, *args):
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args):
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute(query: str, *args):
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def executemany(query: str, args_list):
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.executemany(query, args_list)

# add to core/database.py

async def init_schema():
    """Create required tables if they don't exist"""

    queries = [
        """
CREATE TABLE ticket_panels (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT,
    panel_name TEXT,           -- user-friendly name
    is_active BOOLEAN DEFAULT TRUE

    content TEXT,          -- plain message content
    embed JSONB,           -- full embed structure

    component_type TEXT NOT NULL CHECK (component_type IN ('buttons', 'select')),
    ticket_mode TEXT NOT NULL CHECK (ticket_mode IN ('channel', 'thread')),

    created_at TIMESTAMP DEFAULT NOW()
);
        """,
        """
        CREATE TABLE ticket_panel_buttons (
    id SERIAL PRIMARY KEY,
    panel_id INT REFERENCES ticket_panels(id) ON DELETE CASCADE,

    label TEXT NOT NULL,
    style INT NOT NULL,
    emoji TEXT,

    category_id INT NOT NULL
);
""",
        """
        CREATE TABLE ticket_panel_selects (
    id SERIAL PRIMARY KEY,
    panel_id INT REFERENCES ticket_panels(id) ON DELETE CASCADE,

    label TEXT NOT NULL,
    description TEXT,
    emoji TEXT,

    category_id INT NOT NULL
);
""",
        """
        CREATE TABLE ticket_categories (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,

    name TEXT NOT NULL,

    category_channel_id BIGINT,
    support_role_id BIGINT,

    auto_close BOOLEAN DEFAULT FALSE
);
"""
    ]

    for q in queries:
        await execute(q)
