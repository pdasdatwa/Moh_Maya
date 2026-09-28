from uuid import UUID

from sqlalchemy import String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Relationship(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "relationships"

    from_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    to_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    to_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
