from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Infrastructure(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "infrastructure"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    infra_type: Mapped[str] = mapped_column(String(64), nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    capacity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    dependencies: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
