import os

from aiohttp import web
from rq import Queue

import audio_jobs
import database
from translation_service import translate_transcript
from worker import conn

q = Queue(connection=conn)
api_key = os.environ.get("API_KEY")
admin_key = os.environ.get("ADMIN_KEY")


async def get_transcripts(_request):
    """Get all transcripts"""
    try:
        return web.json_response(await database.get_transcripts())
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def create_transcript(request):
    """Create a new transcript"""

    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized(reason="Invalid API key")

    body = await request.json()
    body["title"] = "placeholder title"
    body["redis_status"] = "pending"
    body["redis_job"] = "pending"
    transcript = await database.insert_transcript(**body)
    body["id"] = transcript["id"]

    if body["media_type"] == "podcast":
        transcript_job = q.enqueue(
            audio_jobs.episode_transcriber,
            timeout=3600,
            **body,
        )
        job_id = transcript_job.id
        status = "started"
    elif body["media_type"] == "youtube":
        transcript_job = q.enqueue(
            audio_jobs.video_transcriber,
            timeout=3600,
            **body,
        )
        job_id = transcript_job.id
        status = "started"
    else:
        status = "failed"
        job_id = None

    episode = await database.update_transcript(
        **{"id": transcript["id"], "redis_job": job_id, "redis_status": status}
    )

    return web.json_response(
        {
            "status": status,
            **episode,
        }
    )


async def create_feed_transcript(request):
    """Create a new transcript for an entire podcast rss feed"""
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        body = await request.json()
        transcript_job = q.enqueue(audio_jobs.feed_transcriber, body["feed_url"])

        try:

            return web.json_response({"status": "success", "job id": transcript_job.id})

        except Exception as e:
            return web.json_response(
                {"status": "failure", "error": f"job not found {e}"}
            )

    except Exception as e:

        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def delete_transcript(request):
    """Delete a transcript"""
    if request.headers.get("admin-key") != admin_key:
        raise web.HTTPUnauthorized()
    _id = request.match_info["id"]
    await database.delete_transcript(_id)
    raise web.HTTPNoContent()


async def update_transcript(request):
    """Update a transcript"""
    if request.headers.get("admin-key") != admin_key:
        raise web.HTTPUnauthorized()
    try:
        _id = request.match_info["id"]
        body = await request.json()
        body["id"] = _id
        return web.json_response(
            await database.update_transcript(
                **body,
            )
        )
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def get_transcript_resource(request):
    """Get a transcript resource"""

    _id = request.match_info["id"]
    transcript = await database.get_transcript_resource(_id)
    if transcript is None:
        raise web.HTTPNotFound()
    return web.json_response(transcript)


async def create_transcript_table(request):
    """Database table creation"""

    if request.headers.get("admin-key") != admin_key:
        raise web.HTTPUnauthorized()
    try:
        await database.create_transcript_table()
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def drop_transcript_table(request):
    """Database table deletion"""

    if request.headers.get("admin-key") != admin_key:
        raise web.HTTPUnauthorized()
    try:
        await database.drop_transcript_table()
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def seed_transcript(request):
    """Seeds the table with fake transcript info"""
    if request.headers.get("admin-key") != admin_key:
        raise web.HTTPUnauthorized()
    body = await request.json()
    try:
        for _ in range(body["transcript_count"]):
            fake_transcript = {
                "title": "Fake title",
                "transcript": "Fake transcript",
                "audio_url": "https://fake.com",
                "media_type": "fake_audio",
            }
            await database.insert_transcript(
                **fake_transcript,
            )
        return web.json_response(
            {"status": "success", "transcript_count": body["transcript_count"]}
        )
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


def html_response(document):
    """Returns an html response"""
    s = open(document, "r")
    return web.Response(text=s.read(), content_type="text/html")


async def documentation(_request):
    """Serves the documentation page"""

    return html_response("./documentation/index.html")


async def change_language(request):
    """Translates a transcript to the target language"""
    _id = request.match_info["id"]
    target_language = request.rel_url.query["target_language"]

    try:
        transcript = await database.get_transcript_resource(_id)
        if transcript is None:
            raise web.HTTPNotFound(reason="transcript not found")

        translated_transcript = translate_transcript(
            text=transcript["google_transcript"],
            target_language=target_language,
        )

        return web.json_response(
            {"status": "success", "transcript": translated_transcript}
        )
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )
