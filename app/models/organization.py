from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorldOwnedMixin


class Organization(UUIDPrimaryKeyMixin, WorldOwnedMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    states: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    roles: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
