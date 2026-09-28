from typing import Any
from uuid import UUID

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    entity_type: str
    entity_id: UUID
    label: str
    properties: dict[str, Any] = {}


class GraphEdge(BaseModel):
    id: str
    relationship_type: str
    source: str
    target: str
    properties: dict[str, Any] = {}


class GraphView(BaseModel):
    world_id: UUID
    nodes: list[GraphNode]
    edges: list[GraphEdge]
