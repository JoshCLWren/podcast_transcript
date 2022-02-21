"""Create and run the AIOHTTP server."""
import os

from aiohttp import web


def get_app():
    app_instance = web.Application()
    from routes import endpoints

    app_instance.add_routes(endpoints())
    web.run_app(app_instance, port=os.getenv("PORT", 8080))


get_app()
