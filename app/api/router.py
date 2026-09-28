from fastapi import APIRouter

from app.api.routes import health, locations, people, simulation, world

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(world.router)
api_router.include_router(locations.router)
api_router.include_router(people.router)
api_router.include_router(simulation.router)
