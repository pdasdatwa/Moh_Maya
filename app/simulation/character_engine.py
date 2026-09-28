from app.schemas.common import format_clock
from app.simulation.context import SimulationContext, mutate_json
from app.simulation.ids import parse_uuid, participant_id


class CharacterEngine:
    """Executes character activity for events that occurred this tick."""

    def process_tick(self, ctx: SimulationContext) -> None:
        clock = format_clock(ctx.world.current_day, ctx.world.current_minute)
        for item in list(ctx.recorded_events):
            if item.get("clock") != clock:
                continue
            specific_type = item.get("specific_type")
            if specific_type == "CafeOpened":
                self._open_cafe(ctx, item)
            elif specific_type == "PersonMorningRoutine":
                self._morning_routine(ctx, item)
            elif specific_type == "PhoneCallReceived":
                self._receive_call(ctx, item)
            elif specific_type == "PersonStartedWork":
                self._go_to_work(ctx, item)

    def _open_cafe(self, ctx: SimulationContext, item: dict) -> None:
        person = ctx.person_by_id(participant_id(item, "opener"))
        consequences = item.get("consequences") or {}
        location = ctx.location_by_id(
            parse_uuid(consequences.get("location_id")) or parse_uuid(item.get("location_id"))
        )
        business = ctx.business_by_id(
            parse_uuid(consequences.get("business_id")) or participant_id(item, "venue")
        )
        if person is None or location is None:
            ctx.note("Could not open cafe: opener or location missing")
            return
        ctx.move_person(person, location, f"{person.name} opened the cafe")
        mutate_json(location, "state", lambda data: data.update({"operational": "open"}))
        if business:
            mutate_json(business, "states", lambda data: data.update({"operational": "open"}))
        ctx.note(f"{person.name} opened the cafe")

    def _morning_routine(self, ctx: SimulationContext, item: dict) -> None:
        person = ctx.person_by_id(participant_id(item, "actor"))
        if person is None:
            return
        pressure = ((ctx.world.world_state or {}).get("environmental") or {}).get("water_pressure")
        if pressure in {"warning", "critical"}:
            ctx.note(f"{person.name} skipped bath: water pressure is {pressure}")
            return
        mutate_json(person, "states", _reduce_fatigue)
        ctx.note(f"{person.name} completed a morning routine")

    def _receive_call(self, ctx: SimulationContext, item: dict) -> None:
        person = ctx.person_by_id(participant_id(item, "recipient"))
        if person is None:
            return
        ctx.note(f"{person.name} received a phone call")

    def _go_to_work(self, ctx: SimulationContext, item: dict) -> None:
        person = ctx.person_by_id(participant_id(item, "worker"))
        consequences = item.get("consequences") or {}
        destination = ctx.location_by_id(
            parse_uuid(consequences.get("location_id")) or parse_uuid(item.get("location_id"))
        )
        if person is None or destination is None:
            ctx.note("Could not go to work: worker or location missing")
            return
        ctx.move_person(person, destination, f"{person.name} left for work")
        ctx.note(f"{person.name} started work at {destination.name}")


def _reduce_fatigue(data: dict) -> None:
    fatigue = dict(data.get("fatigue") or {})
    fatigue["level"] = max(0, int(fatigue.get("level") or 0) - 1)
    fatigue["note"] = "morning_routine"
    data["fatigue"] = fatigue
