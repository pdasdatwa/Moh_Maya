from uuid import UUID

from app.models.enums import WorldStatus
from app.models.location import Location
from app.repositories.infrastructure import InfrastructureRepository
from app.repositories.location import LocationRepository
from app.repositories.natural_entity import NaturalEntityRepository
from app.simulation.context import SimulationContext, mutate_json

PRESSURE_RANK = {"normal": 0, "increasing": 1, "warning": 2, "critical": 3}


class WorldEngine:
    """Authoritative world state and constraint evaluation."""

    def evaluate_conditions(self, ctx: SimulationContext) -> None:
        environmental = dict(ctx.world.world_state.get("environmental") or {})
        if not environmental:
            return
        already = any(note.startswith("World conditions evaluated:") for note in ctx.notes)
        if already:
            return
        ctx.note(
            "World conditions evaluated: "
            f"weather={environmental.get('weather', 'unknown')}"
        )

    def evaluate_constraints(self, ctx: SimulationContext) -> None:
        for infra in InfrastructureRepository(ctx.session).list_for_world(ctx.world.id):
            capacity = infra.capacity or {}
            state = infra.state or {}
            limit = capacity.get("limit")
            used = state.get("used")
            if limit is None or used is None:
                continue
            ratio = used / limit if limit else 0
            pressure = "normal"
            if ratio >= 0.9:
                pressure = "critical"
            elif ratio >= 0.7:
                pressure = "warning"
            elif ratio >= 0.5:
                pressure = "increasing"
            mutate_json(infra, "state", lambda data, p=pressure: data.update({"pressure": p}))
            if pressure != "normal":
                ctx.note(f"Constraint pressure on {infra.name}: {pressure}")

        worst_water = None
        for entity in NaturalEntityRepository(ctx.session).list_for_world(ctx.world.id):
            quantity = (entity.capacity_quantity or {}).get("quantity")
            limit = (entity.capacity_quantity or {}).get("limit")
            pressure = _quantity_pressure(quantity, limit)
            if pressure is None:
                continue
            mutate_json(entity, "state", lambda data, p=pressure: data.update({"pressure": p}))
            worst_water = _worse_pressure(worst_water, pressure)
        if worst_water is not None:
            _write_water_pressure(ctx, worst_water)

    def consume_placeholder_water(self, ctx: SimulationContext) -> None:
        """Tiny deterministic resource movement so an advance updates world resources."""
        for entity in NaturalEntityRepository(ctx.session).list_for_world(ctx.world.id):
            quantity = (entity.capacity_quantity or {}).get("quantity")
            if quantity is None or quantity <= 0:
                continue

            def reduce(data: dict) -> None:
                current = dict(data)
                current["quantity"] = max(0, (current.get("quantity") or 0) - 1)
                data.clear()
                data.update(current)

            mutate_json(entity, "capacity_quantity", reduce)
            remaining = (entity.capacity_quantity or {}).get("quantity")
            limit = (entity.capacity_quantity or {}).get("limit")
            pressure = _quantity_pressure(remaining, limit)
            if pressure is not None:
                mutate_json(entity, "state", lambda data, p=pressure: data.update({"pressure": p}))
                _write_water_pressure(ctx, pressure)
            ctx.note(f"{entity.name} quantity reduced by 1 as placeholder consumption")
            break

    def reject_impossible_move(self, ctx: SimulationContext, location_id: UUID) -> Location:
        location = LocationRepository(ctx.session).get(ctx.world.id, location_id)
        if location is None:
            raise ValueError(
                f"Impossible move: location {location_id} does not exist in this world"
            )
        if ctx.world.status not in {WorldStatus.ADVANCING, WorldStatus.PAUSED}:
            raise ValueError("Impossible move: world is in an unknown status")
        return location


def _quantity_pressure(quantity, limit) -> str | None:
    if quantity is None or limit is None or limit == 0:
        return None
    ratio = quantity / limit
    if ratio <= 0.2:
        return "critical"
    if ratio <= 0.4:
        return "warning"
    if ratio <= 0.6:
        return "increasing"
    return "normal"


def _worse_pressure(current: str | None, candidate: str) -> str:
    if current is None:
        return candidate
    if PRESSURE_RANK.get(candidate, 0) > PRESSURE_RANK.get(current, 0):
        return candidate
    return current


def _write_water_pressure(ctx: SimulationContext, pressure: str) -> None:
    def update(data: dict, value: str = pressure) -> None:
        environmental = dict(data.get("environmental") or {})
        environmental["water_pressure"] = value
        data["environmental"] = environmental

    mutate_json(ctx.world, "world_state", update)
