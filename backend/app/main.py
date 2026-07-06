"""FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload

Feature routers are registered here as each phase lands (auth, timetable,
attendance, assignments, todo, dashboard, coco).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth, health
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {"message": "StudentOS API is running. See /docs for the API reference."}

    return app


app = create_app()
