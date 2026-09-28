from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.location import Location


class LocationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, location_id: UUID) -> Location | None:
        return self.session.scalar(
            select(Location).where(
                Location.world_id == world_id, Location.id == location_id
            )
        )

    def get_by_name(self, world_id: UUID, name: str) -> Location | None:
        return self.session.scalar(
            select(Location).where(Location.world_id == world_id, Location.name == name)
        )

    def list_for_world(self, world_id: UUID) -> list[Location]:
        return list(
            self.session.scalars(
                select(Location).where(Location.world_id == world_id).order_by(Location.name)
            )
        )

    def add(self, location: Location) -> Location:
        self.session.add(location)
        return location
