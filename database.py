import os
import aiopg
import psycopg2.extras

dsn = "dbname=aiopg user=postgres"

DATABASE_URL = os.environ.get("DATABASE_URL")


async def create_transcript_table():
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE transcripts(
                id bigserial PRIMARY KEY,
                podcast_title VARCHAR(255) NOT NULL,
                episode_title VARCHAR(255) NOT NULL,
                transcript TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                rss_url VARCHAR(255) NOT NULL
                );
                """
            )


async def drop_transcript_table():
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DROP TABLE transcript;")


async def insert_transcript(**transcript_data):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute(
                """
            INSERT INTO transcript (podcast_title, episode_title, rss_url, transcript)
            VALUES (%s, %s, %s) RETURNING *;
            """,
                transcript_data,
            )
            return await cur.fetchone()


async def get_transcripts():
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute("SELECT * FROM transcript;")
            return await cur.fetchall()


async def get_transcript_resource(_id):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute("SELECT * FROM transcript WHERE id = %s;", (_id,))
            return await cur.fetchone()


async def delete_transcript(_id):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM transcript WHERE id = %s;", (_id,))


async def update_transcript(**transcript_data):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute(
                """
            UPDATE transcript SET
            podcast_title = %s,
            episode_title = %s,
            rss_url = %s,
            transcript = %s
            WHERE id = %s RETURNING *;
            """,
                transcript_data,
            )
            return await cur.fetchone()
