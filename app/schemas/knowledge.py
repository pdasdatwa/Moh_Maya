from uuid import UUID

from app.schemas.common import ORMModel


class KnowledgeRead(ORMModel):
    id: UUID
    world_id: UUID
    person_id: UUID | None
    subject_entity_type: str | None
    subject_entity_id: UUID | None
    content: str
    knowledge_kind: str
    layer: str
    is_correct: bool
    source: str | None
    established_at_day: int
    established_at_minute: int
    details: dict


class MemoryRead(ORMModel):
    id: UUID
    world_id: UUID
    person_id: UUID
    content: str
    related_event_id: UUID | None
    occurred_at_day: int
    occurred_at_minute: int
    salience: dict
