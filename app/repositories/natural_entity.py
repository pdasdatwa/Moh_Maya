from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.natural_entity import NaturalEntity


class NaturalEntityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, entity_id: UUID) -> NaturalEntity | None:
        return self.session.scalar(
            select(NaturalEntity).where(
                NaturalEntity.world_id == world_id, NaturalEntity.id == entity_id
            )
        )

    def list_for_world(self, world_id: UUID) -> list[NaturalEntity]:
        return list(
            self.session.scalars(
                select(NaturalEntity)
                .where(NaturalEntity.world_id == world_id)
                .order_by(NaturalEntity.name)
            )
        )

    def add(self, entity: NaturalEntity) -> NaturalEntity:
        self.session.add(entity)
        return entity
