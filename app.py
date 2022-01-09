from random import randint
import re
from aiohttp import web
import os
from aiohttp_middlewares import cors_middleware
import database


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
        return web.json_response(await database.get_transcript())
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def create_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        body = await request.json()
        return web.json_response(
            await database.insert_transcript(
                **body,
            )
        )
    except Exception as e:

        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def delete_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        _id = request.match_info["id"]
        await database.delete_transcript(_id)
        raise web.HTTPNoContent()
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


async def update_transcript(request):
    if request.headers.get("api-key") != api_key:
        raise web.HTTPUnauthorized()
    try:
        _id = request.match_info["id"]
        body = await request.json()
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
                "name": fake.name(),
                "description": fake.text(),
                "bit_value": randint(1, 100),
                "channel_point_value": randint(1, 100),
                "description": fake.text(),
                "image_url": f"{fake.url()}/.jpg",
                "custom_message": fake.text(),
            }
            await database.insert_transcript(
                name=fake_transcript["name"],
                description=fake_transcript["description"],
                bit_value=fake_transcript["bit_value"],
                channel_point_value=fake_transcript["channel_point_value"],
                image_url=fake_transcript["image_url"],
                custom_message=fake_transcript["custom_message"],
            )
        return web.json_response(
            {"status": "success", "transcript_count": body["transcript_count"]}
        )
    except Exception as e:
        return web.json_response(
            {"status": "failure", "error": str(e), "type": f"{type(e)}"}
        )


app.add_routes(
    [
        web.get("/", index),
        web.get("/transcript", get_transcripts),
        web.post("/transcript", create_transcript),
        web.delete("/transcript/{id}", delete_transcript),
        web.put("/transcript/{id}", update_transcript),
        web.get("/transcript/{id}", get_transcript_resource),
        web.post("/transcript:create_table", create_transcript_table),
        web.delete("/transcript:drop_table", drop_transcript_table),
        web.post("/transcript:seed", seed_transcript),
    ]
)

web.run_app(app, port=os.getenv("PORT", 8080))
