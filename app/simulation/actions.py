from dataclasses import dataclass, field

from app.models.enums import ActionType
from app.models.world import World
from app.schemas.simulation import PlayerDecision
from app.simulation.ids import parse_uuid

# Placeholder development costs. Not a locked gameplay constant.
WALK_TO_CAFE_MINUTES = 30


@dataclass
class ActionResolution:
    action_type: str
    time_cost_minutes: int
    effects: list[dict] = field(default_factory=list)


class ActionResolver:
    """Maps a player decision to a time cost and placeholder effects."""

    def resolve(self, world: World, decision: PlayerDecision) -> ActionResolution:
        action = decision.action_type.strip().upper()
        if action == ActionType.WAIT:
            if decision.minutes is None or decision.minutes < 1:
                raise ValueError("WAIT requires minutes >= 1")
            return ActionResolution(action_type=action, time_cost_minutes=decision.minutes)
        if action == ActionType.WALK_TO_CAFE:
            location_id = decision.location_id or self._demo_cafe_location_id(world)
            if location_id is None:
                raise ValueError("WALK_TO_CAFE requires a world-scoped location_id")
            return ActionResolution(
                action_type=action,
                time_cost_minutes=WALK_TO_CAFE_MINUTES,
                effects=[
                    {"type": "move_player_to", "location_id": str(location_id)},
                    {"type": "increase_player_fatigue", "amount": 1},
                    {"type": "decrease_player_energy", "amount": 1},
                ],
            )
        raise ValueError(f"Unknown development action: {decision.action_type}")

    def _demo_cafe_location_id(self, world: World):
        demo = (world.world_state or {}).get("demo") or {}
        return parse_uuid(demo.get("walk_to_cafe_location_id"))
