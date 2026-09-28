from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Household(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    resources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    states: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    obligations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
