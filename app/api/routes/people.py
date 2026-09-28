from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.person import PersonRead
from app.services.world_service import WorldNotFoundError, WorldService

router = APIRouter(tags=["people"])


@router.get("/world/{world_id}/people", response_model=list[PersonRead])
def list_people(world_id: UUID, session: Session = Depends(db_session)) -> list[PersonRead]:
    try:
        people = WorldService(session).list_people(world_id)
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [PersonRead.model_validate(person) for person in people]
