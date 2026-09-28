from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Business(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_type: Mapped[str] = mapped_column(String(64), nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    resources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    states: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    goods_services: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    financial_context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
