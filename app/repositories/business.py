from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business import Business


class BusinessRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, business_id: UUID) -> Business | None:
        return self.session.scalar(
            select(Business).where(
                Business.world_id == world_id, Business.id == business_id
            )
        )

    def get_by_name(self, world_id: UUID, name: str) -> Business | None:
        return self.session.scalar(
            select(Business).where(Business.world_id == world_id, Business.name == name)
        )

    def list_for_world(self, world_id: UUID) -> list[Business]:
        return list(
            self.session.scalars(
                select(Business).where(Business.world_id == world_id).order_by(Business.name)
            )
        )

    def add(self, business: Business) -> Business:
        self.session.add(business)
        return business
