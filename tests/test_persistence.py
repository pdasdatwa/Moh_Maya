from sqlalchemy.orm import Session

from app.graph.service import GraphService
from app.models.enums import ActionType
from app.models.world import World
from app.repositories.knowledge import KnowledgeRepository, MemoryRepository
from app.repositories.world import WorldRepository
from app.schemas.simulation import PlayerDecision
from app.simulation.engine import SimulationEngine
from scripts.seed_world import seed_laketown
from tests.conftest import build_cafe_world


def test_knowledge_memory_graph_persist_after_advance(
    session: Session, world: World, session_factory
) -> None:
    fixtures = build_cafe_world(session, world)
    from app.models.enums import EntityType, RelationshipType
    from app.models.relationship import Relationship
    from app.repositories.relationship import RelationshipRepository
    from uuid import uuid4

    RelationshipRepository(session).add(
        Relationship(
            id=uuid4(),
            world_id=world.id,
            from_entity_type=EntityType.PERSON,
            from_entity_id=fixtures["meera"].id,
            to_entity_type=EntityType.PERSON,
            to_entity_id=fixtures["sanjay"].id,
            relationship_type=RelationshipType.KNOWS,
            properties={},
        )
    )
    world_id = world.id
    SimulationEngine(session).advance_decision(
        world.id, PlayerDecision(action_type=ActionType.WALK_TO_CAFE)
    )
    session.commit()

    other = session_factory()
    try:
        knowledge = KnowledgeRepository(other).list_for_world(world_id)
        memories = MemoryRepository(other).list_for_world(world_id)
        assert any("phone call" in record.content.lower() for record in knowledge)
        assert any("phone call" in memory.content.lower() for memory in memories)
        graph = GraphService(other).build(world_id)
        assert any(node.label == "Arjun" for node in graph.nodes)
        assert any(node.entity_type == "event" for node in graph.nodes)
        reloaded = WorldRepository(other).get(world_id)
        assert reloaded is not None
        assert reloaded.current_minute == 510
    finally:
        other.close()


def test_seed_script_against_test_database(session: Session, session_factory) -> None:
    seeded = seed_laketown(session, reset=True)
    assert seeded.name == "Laketown"
    assert seeded.world_state["demo"]["walk_to_cafe_location_id"]

    other = session_factory()
    try:
        loaded = WorldRepository(other).get_by_name("Laketown")
        assert loaded is not None
        assert loaded.id == seeded.id
        assert loaded.current_minute == 480
        demo_id = loaded.world_state["demo"]["walk_to_cafe_location_id"]
        from app.repositories.location import LocationRepository
        from uuid import UUID

        cafe = LocationRepository(other).get(loaded.id, UUID(demo_id))
        assert cafe is not None
        assert cafe.name == "Cafe"
    finally:
        other.close()
