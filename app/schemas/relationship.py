from uuid import UUID

from app.schemas.common import ORMModel


class RelationshipRead(ORMModel):
    id: UUID
    world_id: UUID
    from_entity_type: str
    from_entity_id: UUID
    to_entity_type: str
    to_entity_id: UUID
    relationship_type: str
    properties: dict
