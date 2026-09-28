from copy import deepcopy
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from app.models.enums import EntityType, EventOrigin, EventState
from app.models.person import Person
from app.repositories.event import EventRepository
from app.simulation.context import SimulationContext
from app.simulation.ids import parse_uuid

ACTION_EVENT_TYPES = {
    "open_cafe": "CafeOpened",
    "morning_routine": "PersonMorningRoutine",
    "receive_call": "PhoneCallReceived",
    "go_to_work": "PersonStartedWork",
}


class EventEngine:
    """Scheduled, emergent, and later God events. V1 records causal history."""

    def process_scheduled(self, ctx: SimulationContext) -> None:
        self._resolve_pending(ctx)
        self._materialize_due_schedules(ctx)

    def process_emergent(self, ctx: SimulationContext) -> None:
        """Reserved for condition-driven events. Character schedules cover the V1 demo."""
        return None

    def _resolve_pending(self, ctx: SimulationContext) -> None:
        pending = [
            event
            for event in EventRepository(ctx.session).list_for_world(ctx.world.id)
            if event.state == EventState.PENDING
            and event.occurred_at_day == ctx.world.current_day
            and event.occurred_at_minute == ctx.world.current_minute
        ]
        for event in pending:
            event.state = EventState.RESOLVED
            participants = EventRepository(ctx.session).list_participants(ctx.world.id, event.id)
            ctx.note(f"Scheduled event resolved: {event.specific_type}")
            ctx.recorded_events.append(
                {
                    "id": str(event.id),
                    "specific_type": event.specific_type,
                    "clock": event.history_record.get("clock") if event.history_record else None,
                    "cause": event.cause,
                    "location_id": str(event.location_id) if event.location_id else None,
                    "participants": [
                        {
                            "entity_type": participant.entity_type,
                            "entity_id": str(participant.entity_id),
                            "role": participant.role,
                        }
                        for participant in participants
                    ],
                    "consequences": event.consequences or {},
                }
            )

    def _materialize_due_schedules(self, ctx: SimulationContext) -> None:
        for person in ctx.people:
            schedule = deepcopy(person.schedule or {})
            entries = schedule.get("entries") or []
            changed = False
            for entry in entries:
                if entry.get("fired"):
                    continue
                if entry.get("time_minute") != ctx.world.current_minute:
                    continue
                if entry.get("day") not in (None, ctx.world.current_day):
                    continue
                self._create_from_schedule(ctx, person, entry)
                entry["fired"] = True
                changed = True
            if changed:
                schedule["entries"] = entries
                person.schedule = schedule
                flag_modified(person, "schedule")

    def _create_from_schedule(self, ctx: SimulationContext, person: Person, entry: dict) -> None:
        action = entry.get("action")
        specific_type = ACTION_EVENT_TYPES.get(action)
        if specific_type is None:
            ctx.note(f"{person.name} has an unknown scheduled action: {action}")
            return

        location_id = parse_uuid(entry.get("location_id"))
        business_id = parse_uuid(entry.get("business_id"))
        other_person_id = parse_uuid(entry.get("other_person_id"))
        location = ctx.location_by_id(location_id) or ctx.location_by_id(person.current_location_id)
        participants: list[tuple[str, UUID, str]] = []
        consequences: dict = {"action": action}

        if specific_type == "CafeOpened":
            participants.append((EntityType.PERSON, person.id, "opener"))
            if business_id is not None:
                participants.append((EntityType.BUSINESS, business_id, "venue"))
                consequences["business_id"] = str(business_id)
            if location_id is not None:
                consequences["location_id"] = str(location_id)
                location = ctx.location_by_id(location_id)
        elif specific_type == "PersonMorningRoutine":
            participants.append((EntityType.PERSON, person.id, "actor"))
            consequences["routine"] = "bath"
        elif specific_type == "PhoneCallReceived":
            participants.append((EntityType.PERSON, person.id, "recipient"))
            if other_person_id is not None:
                participants.append((EntityType.PERSON, other_person_id, "caller"))
                consequences["caller_id"] = str(other_person_id)
        elif specific_type == "PersonStartedWork":
            participants.append((EntityType.PERSON, person.id, "worker"))
            if location_id is not None:
                consequences["location_id"] = str(location_id)
                location = ctx.location_by_id(location_id)

        ctx.record_event(
            event_type=EventOrigin.SCHEDULED,
            specific_type=specific_type,
            location=location,
            cause=f"{person.name}'s scheduled {action}",
            consequences=consequences,
            participants=participants,
        )
