from app.models.enums import RelationshipType
from app.repositories.relationship import RelationshipRepository
from app.schemas.common import format_clock
from app.simulation.context import SimulationContext, mutate_json
from app.simulation.ids import person_participant_ids


class RelationshipEngine:
    """Relationship changes over time and through events. Multidimensional later."""

    def process_tick(self, ctx: SimulationContext) -> None:
        clock = format_clock(ctx.world.current_day, ctx.world.current_minute)
        repo = RelationshipRepository(ctx.session)
        for item in ctx.recorded_events:
            if item.get("specific_type") != "PhoneCallReceived":
                continue
            if item.get("clock") != clock:
                continue
            person_ids = person_participant_ids(item)
            if len(person_ids) < 2:
                continue
            relationship = repo.find_between(
                ctx.world.id,
                RelationshipType.KNOWS,
                "person",
                person_ids[0],
                "person",
                person_ids[1],
            )
            if relationship is None:
                continue
            mutate_json(
                relationship,
                "properties",
                lambda data: data.update(
                    {
                        "last_contact_day": ctx.world.current_day,
                        "last_contact_minute": ctx.world.current_minute,
                    }
                ),
            )
            ctx.note("A KNOWS relationship recorded recent contact")
