from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import db_session
from app.schemas.location import LocationRead
from app.services.world_service import WorldNotFoundError, WorldService
from sqlalchemy.orm import Session

router = APIRouter(tags=["locations"])


@router.get("/world/{world_id}/locations", response_model=list[LocationRead])
def list_locations(
    world_id: UUID, session: Session = Depends(db_session)
) -> list[LocationRead]:
    try:
        locations = WorldService(session).list_locations(world_id)
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [LocationRead.model_validate(location) for location in locations]
