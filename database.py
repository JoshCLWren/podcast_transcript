import os
import aiopg
import psycopg2.extras
from datetime_schema import trans_dates_to_string

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
                audio_url VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                rss_url VARCHAR(255) NOT NULL
                );
                """
            )


async def drop_transcript_table():
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DROP TABLE transcripts;")


async def insert_transcript(**transcript_data):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute(
                """
            INSERT INTO transcripts (podcast_title, episode_title, rss_url, transcript, audio_url)
            VALUES (%(podcast_title)s, %(episode_title)s, %(rss_url)s, %(transcript)s, %(audio_url)s) RETURNING *;
            """,
                transcript_data,
            )
            trans = await cur.fetchone()

            return trans_dates_to_string(trans)


async def get_transcripts():
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute("SELECT * FROM transcripts;")

            trans = await cur.fetchall()
            for transcript in trans:
                trans_dates_to_string(transcript)
            return trans


async def get_transcript_resource(_id):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute("SELECT * FROM transcripts WHERE id = %s;", (_id,))

            transcript = await cur.fetchone()
            return trans_dates_to_string(transcript)


async def delete_transcript(_id):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM transcripts WHERE id = %s;", (_id,))


async def update_transcript(**transcript_data):
    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute(
                """
            UPDATE transcripts SET
            podcast_title = %(podcast_title)s,
            episode_title = %(episode_title)s,
            rss_url = %(rss_url)s,
            transcript = %(transcript)s,
            audio_url = %(audio_url)s
            WHERE id = %(id)s RETURNING *;
            """,
                transcript_data,
            )
            transcript = await cur.fetchone()
            return trans_dates_to_string(transcript)
