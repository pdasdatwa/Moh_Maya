from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import WorldStatus


class World(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "worlds"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    current_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorldStatus.PAUSED
    )
    tick_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    calendar: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    world_state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    player_person_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            "people.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_worlds_player_person_id",
        ),
        nullable=True,
    )
