import re
from aiohttp import web
import os
from aiohttp_middlewares import cors_middleware

from handlers import *


cors_rules = cors_middleware(origins=[re.compile(r"(localhost(:[\d]+))?")])
middlewares = [cors_rules]
app = web.Application(middlewares=middlewares)

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
        web.get("/documentation", documentation),
    ]
)

web.run_app(app, port=os.getenv("PORT", 8080))
