from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Item(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "items"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_entity_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
