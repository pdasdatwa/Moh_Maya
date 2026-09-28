from uuid import UUID

from app.schemas.common import ORMModel


class PersonRead(ORMModel):
    id: UUID
    world_id: UUID
    name: str
    age: int
    current_location_id: UUID | None
    household_id: UUID | None
    attributes: dict
    states: dict
    resources: dict
    roles: dict
    goals: dict
    circumstances: dict
    history: list
    schedule: dict
