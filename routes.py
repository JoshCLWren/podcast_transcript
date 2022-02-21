"""Routes for the application."""

from aiohttp import web

from handlers import *


def endpoints():
    return [
        web.get("/", documentation),
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
        web.get("/translate/{id}", change_language),
    ]
