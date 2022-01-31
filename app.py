from random import randint
import re
from time import sleep
from aiohttp import web
import os
from aiohttp_middlewares import cors_middleware
import database
import podcast_transcripter
from rq import Queue
from worker import conn
from utils import _count_words_at_url

q = Queue(connection=conn)


cors_rules = cors_middleware(origins=[re.compile(r"(localhost(:[\d]+))?")])
middlewares = [cors_rules]
app = web.Application(middlewares=middlewares)


api_key = os.environ.get("API_KEY")


async def index(request):
    try:
        await database.create_transcript_table()
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def get_transcripts(request):
    try:
        return web.json_response(await database.get_transcripts())
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def create_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        body = await request.json()

        transcript_job = q.enqueue(
            podcast_transcripter.episode_transcriber,
            **body,
        )

        return web.json_response({"status": "success", "job id": transcript_job.id})

    except Exception as e:

        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def count_words_at_url(request):
    body = await request.json()
    resp = body.get("url")
    result = q.enqueue(_count_words_at_url, resp)
    try:
        sleep(1)
        result = f"results are: {result.result}"
    except:
        result = f"results are not ready yet, job id is: {result.id}"
    return web.json_response({"status": "success", "result": result})


async def create_feed_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        body = await request.json()
        transcript_job = q.enqueue(
            podcast_transcripter.feed_transcriber, body["feed_url"]
        )

        try:

            return web.json_response({"status": "success", "job id": transcript_job.id})

        except:
            return web.json_response({"status": "failure", "error": "job not found"})

    except Exception as e:

        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def delete_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    _id = request.match_info["id"]
    await database.delete_transcript(_id)
    raise web.HTTPNoContent()


async def update_transcript(request):
    if request.headers.get("api-key") != api_key:
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

    _id = request.match_info["id"]
    transcript = await database.get_transcript_resource(_id)
    if transcript is None:
        raise web.HTTPNotFound()
    return web.json_response(transcript)


async def create_transcript_table(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        await database.create_transcript_table()
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def drop_transcript_table(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        await database.drop_transcript_table()
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def seed_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    body = await request.json()
    try:
        for _ in range(body["transcript_count"]):
            fake_transcript = {
                "podcast_title": "Fake Podcast",
                "episode_title": "Fake Episode",
                "rss_url": "https://fake.com",
                "transcript": "Fake transcript",
                "audio_url": "https://fake.com",
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


async def transcribe_video(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    body = await request.json()
    try:
        transcript_job = q.enqueue(
            podcast_transcripter.video_transcriber,
            body["url"],
        )

        return web.json_response({"status": "success", "job id": transcript_job.id})
    except:
        return web.json_response({"status": "failure", "error": "job not found"})


app.add_routes(
    [
        web.get("/", index),
        web.post("/transcripts/-/feed", create_feed_transcript),
        web.get("/transcripts", get_transcripts),
        web.post("/transcripts", create_transcript),
        web.delete("/transcripts/{id}", delete_transcript),
        web.put("/transcripts/{id}", update_transcript),
        web.get("/transcripts/{id}", get_transcript_resource),
        web.post("/transcripts:create_table", create_transcript_table),
        web.delete("/transcripts:drop_table", drop_transcript_table),
        web.post("/transcripts:seed", seed_transcript),
        web.post("/count", count_words_at_url),
        web.post("/transcripts:video", transcribe_video),
    ]
)

web.run_app(app, port=os.getenv("PORT", 8080))
