from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerDecision(BaseModel):
    action_type: str = Field(description="Development action such as WAIT or WALK_TO_CAFE")
    minutes: int | None = Field(
        default=None, description="Optional WAIT duration in game minutes"
    )
    location_id: UUID | None = Field(
        default=None,
        description="World-scoped destination for WALK_TO_CAFE. Optional when the world stores a demo cafe id.",
    )


class AdvanceSummary(BaseModel):
    world_id: UUID
    action_type: str
    time_cost_minutes: int
    ticks_processed: int
    started_clock: str
    ended_clock: str
    status: str
    events: list[dict[str, Any]]
    notes: list[str]
