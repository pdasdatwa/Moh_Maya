from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class KnowledgeRecord(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_records"

    person_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=True, index=True
    )
    subject_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject_entity_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    layer: Mapped[str] = mapped_column(String(32), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    established_at_day: Mapped[int] = mapped_column(Integer, nullable=False)
    established_at_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Memory(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "memories"

    person_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    related_event_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at_day: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    salience: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
