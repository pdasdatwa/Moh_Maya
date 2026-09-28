from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import WorldStatus
from app.models.world import World
from app.repositories.world import WorldRepository
from app.schemas.common import format_clock
from app.schemas.simulation import AdvanceSummary, PlayerDecision
from app.simulation.actions import ActionResolver
from app.simulation.character_engine import CharacterEngine
from app.simulation.context import SimulationContext, mutate_json
from app.simulation.economy_engine import EconomyEngine
from app.simulation.event_engine import EventEngine
from app.simulation.government_engine import GovernmentEngine
from app.simulation.health_engine import HealthEngine
from app.simulation.ids import parse_uuid
from app.simulation.knowledge_engine import KnowledgeEngine
from app.simulation.relationship_engine import RelationshipEngine
from app.simulation.world_engine import WorldEngine


class SimulationEngine:
    """Orchestrates one coherent advance, then returns the world to PAUSED."""

    def __init__(
        self,
        session: Session,
        fail_after_tick: int | None = None,
    ) -> None:
        self.session = session
        self.fail_after_tick = fail_after_tick
        self.world_engine = WorldEngine()
        self.character_engine = CharacterEngine()
        self.event_engine = EventEngine()
        self.health_engine = HealthEngine()
        self.economy_engine = EconomyEngine()
        self.relationship_engine = RelationshipEngine()
        self.knowledge_engine = KnowledgeEngine()
        self.government_engine = GovernmentEngine()
        self.action_resolver = ActionResolver()

    def advance_decision(self, world_id: UUID, decision: PlayerDecision) -> AdvanceSummary:
        world = self._require_world(world_id)
        resolution = self.action_resolver.resolve(world, decision)
        ticks = max(1, ceil(resolution.time_cost_minutes / world.tick_minutes))
        return self.advance(
            world_id,
            ticks,
            action_type=resolution.action_type,
            time_cost_minutes=resolution.time_cost_minutes,
            pending_effects=resolution.effects,
        )

    def advance(
        self,
        world_id: UUID,
        ticks: int,
        action_type: str = "ADVANCE",
        time_cost_minutes: int | None = None,
        pending_effects: list[dict] | None = None,
    ) -> AdvanceSummary:
        if ticks < 1:
            raise ValueError("ticks must be >= 1")

        world = self._require_world(world_id)
        started_clock = format_clock(world.current_day, world.current_minute)
        ctx = SimulationContext(
            session=self.session,
            world=world,
            pending_effects=pending_effects or [],
        )
        ctx.load()

        world.status = WorldStatus.ADVANCING
        self.session.flush()

        water_consumed = False
        for tick_index in range(ticks):
            self._advance_clock(world)
            ctx.load()
            self.world_engine.evaluate_conditions(ctx)
            self.world_engine.evaluate_constraints(ctx)
            if not water_consumed:
                self.world_engine.consume_placeholder_water(ctx)
                water_consumed = True
            self.event_engine.process_scheduled(ctx)
            self.event_engine.process_emergent(ctx)
            self.character_engine.process_tick(ctx)
            self.health_engine.process_tick(ctx)
            self.economy_engine.process_tick(ctx)
            self.relationship_engine.process_tick(ctx)
            self.knowledge_engine.process_tick(ctx)
            self.government_engine.process_tick(ctx)
            if self.fail_after_tick is not None and tick_index + 1 >= self.fail_after_tick:
                raise RuntimeError("Injected simulation failure")

        self._apply_pending_effects(ctx)
        world.status = WorldStatus.PAUSED
        self.session.flush()

        return AdvanceSummary(
            world_id=world.id,
            action_type=action_type,
            time_cost_minutes=time_cost_minutes or ticks * world.tick_minutes,
            ticks_processed=ticks,
            started_clock=started_clock,
            ended_clock=format_clock(world.current_day, world.current_minute),
            status=world.status,
            events=ctx.recorded_events,
            notes=ctx.notes,
        )

    def _require_world(self, world_id: UUID) -> World:
        world = WorldRepository(self.session).get(world_id)
        if world is None:
            raise KeyError(f"World {world_id} not found")
        return world

    def _advance_clock(self, world: World) -> None:
        total = world.current_minute + world.tick_minutes
        world.current_day += total // 1440
        world.current_minute = total % 1440

    def _apply_pending_effects(self, ctx: SimulationContext) -> None:
        player = ctx.person_by_id(ctx.world.player_person_id)
        for effect in ctx.pending_effects:
            effect_type = effect.get("type")
            if effect_type == "move_player_to":
                location_id = parse_uuid(effect.get("location_id"))
                if location_id is None:
                    raise ValueError("Impossible move: location_id missing")
                location = self.world_engine.reject_impossible_move(ctx, location_id)
                if player is None:
                    raise ValueError("Impossible move: player missing")
                ctx.move_person(player, location, "Player completed WALK_TO_CAFE")
                ctx.note(f"{player.name} arrived at {location.name}")
            elif effect_type == "increase_player_fatigue":
                if player is None:
                    continue
                amount = int(effect.get("amount") or 1)

                def bump(data: dict, delta: int = amount) -> None:
                    fatigue = dict(data.get("fatigue") or {})
                    fatigue["level"] = int(fatigue.get("level") or 0) + delta
                    fatigue["note"] = "walk"
                    data["fatigue"] = fatigue

                mutate_json(player, "states", bump)
                ctx.note(f"{player.name} fatigue increased from walking")
            elif effect_type == "decrease_player_energy":
                if player is None:
                    continue
                amount = int(effect.get("amount") or 1)

                def drain(data: dict, delta: int = amount) -> None:
                    energy = dict(data.get("energy") or {})
                    energy["available"] = int(energy.get("available") or 0) - delta
                    data["energy"] = energy

                mutate_json(player, "resources", drain)
                ctx.note(f"{player.name} energy decreased from walking")
