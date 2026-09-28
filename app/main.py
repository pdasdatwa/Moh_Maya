from fastapi import FastAPI

from app.api.router import api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Moh Maya",
        description=(
            "Developer/God inspection API for the Moh Maya simulation. "
            "GET /worlds, /world/{id}, knowledge, memories, graph, and related "
            "routes expose authoritative world state for engineering and debugging. "
            "They are not a player-facing knowledge surface and do not filter by "
            "player perception."
        ),
        version="0.1.0",
    )
    application.include_router(api_router)
    return application


app = create_app()
