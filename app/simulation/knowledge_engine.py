from uuid import UUID

from app.models.enums import KnowledgeKind, KnowledgeLayer
from app.models.knowledge import KnowledgeRecord, Memory
from app.repositories.knowledge import KnowledgeRepository, MemoryRepository
from app.schemas.common import format_clock
from app.simulation.context import SimulationContext
from app.simulation.ids import participant_id


class KnowledgeEngine:
    """Persistence foundation for what is true, known, believed, or remembered."""

    def process_tick(self, ctx: SimulationContext) -> None:
        clock = format_clock(ctx.world.current_day, ctx.world.current_minute)
        for item in ctx.recorded_events:
            if item.get("specific_type") != "PhoneCallReceived":
                continue
            if item.get("clock") != clock:
                continue
            recipient = ctx.person_by_id(participant_id(item, "recipient"))
            if recipient is None:
                continue
            KnowledgeRepository(ctx.session).add(
                KnowledgeRecord(
                    world_id=ctx.world.id,
                    person_id=recipient.id,
                    subject_entity_type=None,
                    subject_entity_id=None,
                    content="Received a morning phone call.",
                    knowledge_kind=KnowledgeKind.FACT,
                    layer=KnowledgeLayer.PERSON,
                    is_correct=True,
                    source="phone_call",
                    established_at_day=ctx.world.current_day,
                    established_at_minute=ctx.world.current_minute,
                    details={},
                )
            )
            event_id = item.get("id")
            MemoryRepository(ctx.session).add(
                Memory(
                    world_id=ctx.world.id,
                    person_id=recipient.id,
                    content="I took a phone call this morning.",
                    related_event_id=UUID(event_id) if event_id else None,
                    occurred_at_day=ctx.world.current_day,
                    occurred_at_minute=ctx.world.current_minute,
                    salience={"placeholder": True},
                )
            )
            ctx.note(f"{recipient.name} stored knowledge and a memory of the phone call")
