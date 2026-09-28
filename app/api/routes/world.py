from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.graph.service import GraphService
from app.schemas.event import EventRead
from app.schemas.graph import GraphView
from app.schemas.knowledge import KnowledgeRead, MemoryRead
from app.schemas.relationship import RelationshipRead
from app.schemas.world import WorldRead
from app.services.world_service import WorldNotFoundError, WorldService

router = APIRouter(tags=["world"])


def _service(session: Session = Depends(db_session)) -> WorldService:
    return WorldService(session)


@router.get(
    "/worlds",
    response_model=list[WorldRead],
    summary="List worlds (God inspect)",
)
def list_worlds(service: WorldService = Depends(_service)) -> list[WorldRead]:
    return [WorldRead.model_validate(world) for world in service.list_worlds()]


@router.get("/world/{world_id}", response_model=WorldRead)
def get_world(world_id: UUID, service: WorldService = Depends(_service)) -> WorldRead:
    try:
        return WorldRead.model_validate(service.get_world(world_id))
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/world/{world_id}/events", response_model=list[EventRead])
def list_events(world_id: UUID, service: WorldService = Depends(_service)) -> list[EventRead]:
    try:
        return [EventRead.model_validate(event) for event in service.list_events(world_id)]
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/world/{world_id}/relationships", response_model=list[RelationshipRead])
def list_relationships(
    world_id: UUID, service: WorldService = Depends(_service)
) -> list[RelationshipRead]:
    try:
        return [
            RelationshipRead.model_validate(rel)
            for rel in service.list_relationships(world_id)
        ]
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/world/{world_id}/knowledge",
    response_model=list[KnowledgeRead],
    summary="List knowledge records (God inspect)",
)
def list_knowledge(
    world_id: UUID, service: WorldService = Depends(_service)
) -> list[KnowledgeRead]:
    try:
        return [
            KnowledgeRead.model_validate(record)
            for record in service.list_knowledge(world_id)
        ]
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/world/{world_id}/memories",
    response_model=list[MemoryRead],
    summary="List memories (God inspect)",
)
def list_memories(
    world_id: UUID, service: WorldService = Depends(_service)
) -> list[MemoryRead]:
    try:
        return [MemoryRead.model_validate(memory) for memory in service.list_memories(world_id)]
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/world/{world_id}/graph", response_model=GraphView)
def get_graph(world_id: UUID, session: Session = Depends(db_session)) -> GraphView:
    try:
        return GraphService(session).build(world_id)
    except WorldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
