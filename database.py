import os

import aiopg
import psycopg2.extras

from datetime_schema import trans_dates_to_string

dsn = "dbname=aiopg user=postgres"

DATABASE_URL = os.environ.get("DATABASE_URL")

TRANSCRIPT_COLUMNS = {
    "id": "bigserial PRIMARY KEY",
    "title": "VARCHAR(255)",
    "audio_url": "VARCHAR(255) NOT NULL",
    "media_type": "VARCHAR(50) NOT NULL",
    "redis_status": "VARCHAR(255)",
    "redis_job": "VARCHAR(255)",
    "google_transcript": "TEXT",
    "wit_ai_transcript": "TEXT",
    "error_message": "TEXT",
    "created_at": "TIMESTAMP NOT NULL DEFAULT NOW()",
    "updated_at": "TIMESTAMP NOT NULL DEFAULT NOW()",
}


async def create_transcript_table():
    """Create the transcript table"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            sql = "CREATE TABLE IF NOT EXISTS transcripts ("
            sql += ", ".join(
                f"{key} {value}" for key, value in TRANSCRIPT_COLUMNS.items()
            )
            sql += ");"
            await cur.execute(sql)


async def drop_transcript_table():
    """Drop the transcript table"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DROP TABLE transcripts;")


async def insert_transcript(**transcript_data):
    """Insert a transcript into the DB"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

            transcript_input = _normalize_columns(transcript_data)

            sql = "INSERT INTO transcripts ("
            sql += ", ".join(transcript_input.keys())
            sql += ") VALUES ("
            sql += ", ".join([f"%({key})s" for key in transcript_input.keys()])
            sql += ") RETURNING *;"

            await cur.execute(
                sql,
                transcript_input,
            )

            transcript = await cur.fetchone()

            return trans_dates_to_string(transcript)


async def get_transcripts():
    """Get all transcripts from the DB"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute("SELECT * FROM transcripts order by created_at desc;")

            trans = await cur.fetchall()
            for transcript in trans:
                trans_dates_to_string(transcript)
            return trans


async def get_transcript_resource(_id):
    """Get a transcript from the DB"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            await cur.execute("SELECT * FROM transcripts WHERE id = %s;", (_id,))

            transcript = await cur.fetchone()
            return trans_dates_to_string(transcript)


async def delete_transcript(_id):
    """Delete a transcript from the DB"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM transcripts WHERE id = %s;", (_id,))


async def update_transcript(**transcript_data):
    """Update a transcript in the DB"""

    async with aiopg.connect(DATABASE_URL) as conn:
        async with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

            if "id" not in transcript_data:
                return await insert_transcript(**transcript_data)

            transcript_input = _normalize_columns(transcript_data)

            sql = "UPDATE transcripts SET "

            sql += "".join(
                f"{key} = %({key})s, " for key, _value in transcript_input.items()
            )

            sql += "updated_at = NOW() WHERE id = %(id)s RETURNING *;"

            await cur.execute(
                sql,
                transcript_input,
            )
            transcript = await cur.fetchone()
            return trans_dates_to_string(transcript)


def _normalize_columns(transcript_data):
    """Ensure that any superfluous keys get dropped of dictionaries before getting to the DB"""

    return {
        key: transcript_data[key]
        for key in transcript_data.keys()
        if key in TRANSCRIPT_COLUMNS
    }
