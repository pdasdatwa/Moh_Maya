from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class NaturalEntity(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "natural_entities"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    natural_type: Mapped[str] = mapped_column(String(64), nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    capacity_quantity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
