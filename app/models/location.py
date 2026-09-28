from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Location(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location_type: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    capacity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
