from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def format_clock(day: int, minute: int) -> str:
    hours, mins = divmod(minute, 60)
    return f"Day {day}, {hours:02d}:{mins:02d}"


class EntityRef(BaseModel):
    entity_type: str
    entity_id: UUID
    name: str | None = None
