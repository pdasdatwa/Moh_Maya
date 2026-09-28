from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin
from app.models.enums import EventState


class Event(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "events"

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    specific_type: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at_day: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EventState.RESOLVED
    )
    consequences: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    history_record: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class EventParticipant(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "event_participants"

    event_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="participant")
