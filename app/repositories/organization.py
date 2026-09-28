from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, organization_id: UUID) -> Organization | None:
        return self.session.scalar(
            select(Organization).where(
                Organization.world_id == world_id, Organization.id == organization_id
            )
        )

    def list_for_world(self, world_id: UUID) -> list[Organization]:
        return list(
            self.session.scalars(
                select(Organization)
                .where(Organization.world_id == world_id)
                .order_by(Organization.name)
            )
        )

    def add(self, organization: Organization) -> Organization:
        self.session.add(organization)
        return organization
