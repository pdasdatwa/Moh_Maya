from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.relationship import Relationship


class RelationshipRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_world(self, world_id: UUID) -> list[Relationship]:
        return list(
            self.session.scalars(
                select(Relationship)
                .where(Relationship.world_id == world_id)
                .order_by(Relationship.relationship_type)
            )
        )

    def find(
        self,
        world_id: UUID,
        from_entity_type: str,
        from_entity_id: UUID,
        relationship_type: str,
    ) -> Relationship | None:
        return self.session.scalar(
            select(Relationship).where(
                Relationship.world_id == world_id,
                Relationship.from_entity_type == from_entity_type,
                Relationship.from_entity_id == from_entity_id,
                Relationship.relationship_type == relationship_type,
            )
        )

    def find_between(
        self,
        world_id: UUID,
        relationship_type: str,
        entity_type_a: str,
        entity_id_a: UUID,
        entity_type_b: str,
        entity_id_b: UUID,
    ) -> Relationship | None:
        return self.session.scalar(
            select(Relationship).where(
                Relationship.world_id == world_id,
                Relationship.relationship_type == relationship_type,
                or_(
                    and_(
                        Relationship.from_entity_type == entity_type_a,
                        Relationship.from_entity_id == entity_id_a,
                        Relationship.to_entity_type == entity_type_b,
                        Relationship.to_entity_id == entity_id_b,
                    ),
                    and_(
                        Relationship.from_entity_type == entity_type_b,
                        Relationship.from_entity_id == entity_id_b,
                        Relationship.to_entity_type == entity_type_a,
                        Relationship.to_entity_id == entity_id_a,
                    ),
                ),
            )
        )

    def add(self, relationship: Relationship) -> Relationship:
        self.session.add(relationship)
        return relationship
