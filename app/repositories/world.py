from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.world import World


class WorldRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID) -> World | None:
        return self.session.get(World, world_id)

    def get_by_name(self, name: str) -> World | None:
        return self.session.scalar(select(World).where(World.name == name))

    def list_all(self) -> list[World]:
        return list(self.session.scalars(select(World).order_by(World.name)))

    def add(self, world: World) -> World:
        self.session.add(world)
        return world
