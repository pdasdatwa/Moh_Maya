from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel, format_clock


class WorldRead(ORMModel):
    id: UUID
    name: str
    current_day: int
    current_minute: int
    status: str
    tick_minutes: int
    calendar: dict
    world_state: dict
    history: list
    player_person_id: UUID | None
    clock: str = Field(default="")

    def model_post_init(self, __context: object) -> None:
        object.__setattr__(
            self, "clock", format_clock(self.current_day, self.current_minute)
        )
