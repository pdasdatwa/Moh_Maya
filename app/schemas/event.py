from uuid import UUID

from app.schemas.common import ORMModel, format_clock


class EventRead(ORMModel):
    id: UUID
    world_id: UUID
    event_type: str
    specific_type: str
    occurred_at_day: int
    occurred_at_minute: int
    location_id: UUID | None
    cause: str | None
    state: str
    consequences: dict
    history_record: dict
    clock: str = ""

    def model_post_init(self, __context: object) -> None:
        object.__setattr__(
            self,
            "clock",
            format_clock(self.occurred_at_day, self.occurred_at_minute),
        )
