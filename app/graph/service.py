from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import EntityType
from app.repositories.business import BusinessRepository
from app.repositories.event import EventRepository
from app.repositories.household import HouseholdRepository
from app.repositories.infrastructure import InfrastructureRepository
from app.repositories.item import ItemRepository
from app.repositories.location import LocationRepository
from app.repositories.natural_entity import NaturalEntityRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository
from app.repositories.world import WorldRepository
from app.schemas.graph import GraphEdge, GraphNode, GraphView
from app.services.world_service import WorldNotFoundError


def node_id(entity_type: str, entity_id: UUID) -> str:
    return f"{entity_type}:{entity_id}"


class GraphService:
    """Builds a nodes/edges view from PostgreSQL. Safe to remove."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def build(self, world_id: UUID) -> GraphView:
        world = WorldRepository(self.session).get(world_id)
        if world is None:
            raise WorldNotFoundError(f"World {world_id} not found")

        nodes: list[GraphNode] = [
            GraphNode(
                id=node_id(EntityType.WORLD, world.id),
                entity_type=EntityType.WORLD,
                entity_id=world.id,
                label=world.name,
                properties={"status": world.status, "clock_day": world.current_day},
            )
        ]

        def add(entity_type: str, entity_id: UUID, label: str, properties: dict | None = None) -> None:
            nodes.append(
                GraphNode(
                    id=node_id(entity_type, entity_id),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    label=label,
                    properties=properties or {},
                )
            )

        for location in LocationRepository(self.session).list_for_world(world_id):
            add(EntityType.LOCATION, location.id, location.name, {"location_type": location.location_type})
        for person in PersonRepository(self.session).list_for_world(world_id):
            add(EntityType.PERSON, person.id, person.name, {"age": person.age})
        for household in HouseholdRepository(self.session).list_for_world(world_id):
            add(EntityType.HOUSEHOLD, household.id, household.name)
        for organization in OrganizationRepository(self.session).list_for_world(world_id):
            add(EntityType.ORGANIZATION, organization.id, organization.name, {"org_type": organization.org_type})
        for business in BusinessRepository(self.session).list_for_world(world_id):
            add(EntityType.BUSINESS, business.id, business.name, {"business_type": business.business_type})
        for infra in InfrastructureRepository(self.session).list_for_world(world_id):
            add(EntityType.INFRASTRUCTURE, infra.id, infra.name, {"infra_type": infra.infra_type})
        for entity in NaturalEntityRepository(self.session).list_for_world(world_id):
            add(EntityType.NATURAL_ENTITY, entity.id, entity.name, {"natural_type": entity.natural_type})
        for item in ItemRepository(self.session).list_for_world(world_id):
            add(EntityType.ITEM, item.id, item.name, {"item_type": item.item_type})
        for event in EventRepository(self.session).list_for_world(world_id):
            add(
                EntityType.EVENT,
                event.id,
                event.specific_type,
                {"event_type": event.event_type, "state": event.state},
            )

        known_ids = {node.id for node in nodes}
        edges: list[GraphEdge] = []
        for rel in RelationshipRepository(self.session).list_for_world(world_id):
            source = node_id(rel.from_entity_type, rel.from_entity_id)
            target = node_id(rel.to_entity_type, rel.to_entity_id)
            if source not in known_ids or target not in known_ids:
                continue
            edges.append(
                GraphEdge(
                    id=str(rel.id),
                    relationship_type=rel.relationship_type,
                    source=source,
                    target=target,
                    properties=rel.properties or {},
                )
            )

        return GraphView(world_id=world_id, nodes=nodes, edges=edges)
