from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.infrastructure import Infrastructure


class InfrastructureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, infrastructure_id: UUID) -> Infrastructure | None:
        return self.session.scalar(
            select(Infrastructure).where(
                Infrastructure.world_id == world_id, Infrastructure.id == infrastructure_id
            )
        )

    def list_for_world(self, world_id: UUID) -> list[Infrastructure]:
        return list(
            self.session.scalars(
                select(Infrastructure)
                .where(Infrastructure.world_id == world_id)
                .order_by(Infrastructure.name)
            )
        )

    def add(self, infrastructure: Infrastructure) -> Infrastructure:
        self.session.add(infrastructure)
        return infrastructure
