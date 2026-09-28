from uuid import UUID

from app.schemas.common import ORMModel


class LocationRead(ORMModel):
    id: UUID
    world_id: UUID
    name: str
    location_type: str
    parent_location_id: UUID | None
    state: dict
    capacity: dict
    properties: dict
