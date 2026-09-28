from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.simulation import AdvanceSummary, PlayerDecision
from app.services.world_service import WorldNotFoundError, WorldService
from app.simulation.engine import SimulationEngine


class SimulationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.worlds = WorldService(session)
        self.engine = SimulationEngine(session)

    def advance(self, world_id: UUID, decision: PlayerDecision) -> AdvanceSummary:
        self.worlds.get_world(world_id)
        try:
            return self.engine.advance_decision(world_id, decision)
        except KeyError as exc:
            raise WorldNotFoundError(str(exc)) from exc
