from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeRecord, Memory


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, record_id: UUID) -> KnowledgeRecord | None:
        return self.session.scalar(
            select(KnowledgeRecord).where(
                KnowledgeRecord.world_id == world_id, KnowledgeRecord.id == record_id
            )
        )

    def list_for_world(self, world_id: UUID) -> list[KnowledgeRecord]:
        return list(
            self.session.scalars(
                select(KnowledgeRecord).where(KnowledgeRecord.world_id == world_id)
            )
        )

    def add(self, record: KnowledgeRecord) -> KnowledgeRecord:
        self.session.add(record)
        return record


class MemoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, memory_id: UUID) -> Memory | None:
        return self.session.scalar(
            select(Memory).where(Memory.world_id == world_id, Memory.id == memory_id)
        )

    def list_for_world(self, world_id: UUID) -> list[Memory]:
        return list(self.session.scalars(select(Memory).where(Memory.world_id == world_id)))

    def add(self, memory: Memory) -> Memory:
        self.session.add(memory)
        return memory
