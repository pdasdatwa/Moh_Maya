from uuid import uuid4

from sqlalchemy.orm import Session

from app.graph.service import GraphService
from app.models.enums import EntityType, RelationshipType
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.relationship import RelationshipRepository
from tests.conftest import add_location, add_person


def test_graph_representation_generation(session: Session, world: World) -> None:
    square = add_location(session, world, "Town Square")
    person = add_person(session, world, "Arjun", location=square)
    RelationshipRepository(session).add(
        Relationship(
            id=uuid4(),
            world_id=world.id,
            from_entity_type=EntityType.PERSON,
            from_entity_id=person.id,
            to_entity_type=EntityType.LOCATION,
            to_entity_id=square.id,
            relationship_type=RelationshipType.LOCATED_AT,
            properties={},
        )
    )
    session.flush()

    graph = GraphService(session).build(world.id)
    node_types = {node.entity_type for node in graph.nodes}
    assert EntityType.WORLD in node_types
    assert EntityType.LOCATION in node_types
    assert EntityType.PERSON in node_types
    assert any(node.label == "Arjun" for node in graph.nodes)
    assert any(edge.relationship_type == RelationshipType.LOCATED_AT for edge in graph.edges)
    assert all(edge.source in {node.id for node in graph.nodes} for edge in graph.edges)
