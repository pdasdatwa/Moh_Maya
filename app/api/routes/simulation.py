from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.simulation import AdvanceSummary, PlayerDecision
from app.services.simulation_service import SimulationService
from app.services.world_service import WorldNotFoundError

router = APIRouter(tags=["simulation"])


@router.post("/world/{world_id}/simulation/advance", response_model=AdvanceSummary)
def advance_simulation(
    world_id: UUID,
    decision: PlayerDecision,
    session: Session = Depends(db_session),
) -> AdvanceSummary:
    try:
        return SimulationService(session).advance(world_id, decision)
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
