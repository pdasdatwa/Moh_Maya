from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Person(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "people"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    current_location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    household_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("households.id", ondelete="SET NULL"), nullable=True
    )
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    states: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    roles: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    goals: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    circumstances: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    schedule: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
