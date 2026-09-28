from uuid import uuid4

from sqlalchemy.orm import Session

from app.graph.service import GraphService
from app.models.enums import EntityType, KnowledgeKind, KnowledgeLayer, RelationshipType
from app.models.knowledge import KnowledgeRecord, Memory
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.business import BusinessRepository
from app.repositories.event import EventRepository
from app.repositories.household import HouseholdRepository
from app.repositories.knowledge import KnowledgeRepository, MemoryRepository
from app.repositories.location import LocationRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository
from app.repositories.world import WorldRepository
from app.schemas.simulation import PlayerDecision
from app.simulation.engine import SimulationEngine
from tests.conftest import (
    add_business,
    add_household,
    add_location,
    add_person,
    build_cafe_world,
)


def _other_world(session: Session) -> World:
    world_b = World(
        name=f"other-world-{uuid4()}",
        current_day=1,
        current_minute=0,
        status="paused",
        tick_minutes=1,
        calendar={},
        world_state={},
        history=[],
    )
    WorldRepository(session).add(world_b)
    session.flush()
    return world_b


def test_world_isolation(session: Session, world: World) -> None:
    world_b = _other_world(session)

    loc_a = add_location(session, world, "Cafe A")
    loc_b = add_location(session, world_b, "Cafe B")
    person_a = add_person(session, world, "Sanjay", location=loc_a)
    person_b = add_person(session, world_b, "Sanjay", location=loc_b)

    people_a = PersonRepository(session).list_for_world(world.id)
    people_b = PersonRepository(session).list_for_world(world_b.id)
    locations_a = LocationRepository(session).list_for_world(world.id)
    locations_b = LocationRepository(session).list_for_world(world_b.id)
    events_a = EventRepository(session).list_for_world(world.id)
    events_b = EventRepository(session).list_for_world(world_b.id)

    assert {person.id for person in people_a} == {person_a.id}
    assert {person.id for person in people_b} == {person_b.id}
    assert {location.id for location in locations_a} == {loc_a.id}
    assert {location.id for location in locations_b} == {loc_b.id}
    assert events_a == []
    assert events_b == []
    assert PersonRepository(session).get(world.id, person_b.id) is None
    assert LocationRepository(session).get(world.id, loc_b.id) is None


def test_business_household_relationship_isolation(session: Session, world: World) -> None:
    world_b = _other_world(session)
    loc_a = add_location(session, world, "Square A")
    loc_b = add_location(session, world_b, "Square B")
    household_a = add_household(session, world, "House A", loc_a)
    household_b = add_household(session, world_b, "House B", loc_b)
    business_a = add_business(session, world, "Cafe A", location=loc_a)
    business_b = add_business(session, world_b, "Cafe B", location=loc_b)
    person_a = add_person(session, world, "Asha", location=loc_a, household=household_a)
    person_b = add_person(session, world_b, "Asha", location=loc_b, household=household_b)

    rel_a = Relationship(
        id=uuid4(),
        world_id=world.id,
        from_entity_type=EntityType.PERSON,
        from_entity_id=person_a.id,
        to_entity_type=EntityType.PERSON,
        to_entity_id=person_a.id,
        relationship_type=RelationshipType.KNOWS,
        properties={"world": "a"},
    )
    rel_b = Relationship(
        id=uuid4(),
        world_id=world_b.id,
        from_entity_type=EntityType.PERSON,
        from_entity_id=person_b.id,
        to_entity_type=EntityType.PERSON,
        to_entity_id=person_b.id,
        relationship_type=RelationshipType.KNOWS,
        properties={"world": "b"},
    )
    RelationshipRepository(session).add(rel_a)
    RelationshipRepository(session).add(rel_b)
    session.flush()

    assert BusinessRepository(session).get(world.id, business_b.id) is None
    assert HouseholdRepository(session).get(world.id, household_b.id) is None
    assert {row.id for row in BusinessRepository(session).list_for_world(world.id)} == {business_a.id}
    assert {row.id for row in HouseholdRepository(session).list_for_world(world.id)} == {household_a.id}
    rels_a = RelationshipRepository(session).list_for_world(world.id)
    assert {row.id for row in rels_a} == {rel_a.id}
    assert RelationshipRepository(session).find_between(
        world.id, RelationshipType.KNOWS, EntityType.PERSON, person_b.id, EntityType.PERSON, person_b.id
    ) is None


def test_knowledge_memory_isolation(session: Session, world: World) -> None:
    world_b = _other_world(session)
    person_a = add_person(session, world, "Meera")
    person_b = add_person(session, world_b, "Meera")
    knowledge_a = KnowledgeRecord(
        id=uuid4(),
        world_id=world.id,
        person_id=person_a.id,
        content="World A fact",
        knowledge_kind=KnowledgeKind.FACT,
        layer=KnowledgeLayer.PERSON,
        is_correct=True,
        source="test",
        established_at_day=1,
        established_at_minute=0,
        details={},
    )
    knowledge_b = KnowledgeRecord(
        id=uuid4(),
        world_id=world_b.id,
        person_id=person_b.id,
        content="World B fact",
        knowledge_kind=KnowledgeKind.FACT,
        layer=KnowledgeLayer.PERSON,
        is_correct=True,
        source="test",
        established_at_day=1,
        established_at_minute=0,
        details={},
    )
    memory_a = Memory(
        id=uuid4(),
        world_id=world.id,
        person_id=person_a.id,
        content="World A memory",
        occurred_at_day=1,
        occurred_at_minute=0,
        salience={},
    )
    memory_b = Memory(
        id=uuid4(),
        world_id=world_b.id,
        person_id=person_b.id,
        content="World B memory",
        occurred_at_day=1,
        occurred_at_minute=0,
        salience={},
    )
    KnowledgeRepository(session).add(knowledge_a)
    KnowledgeRepository(session).add(knowledge_b)
    MemoryRepository(session).add(memory_a)
    MemoryRepository(session).add(memory_b)
    session.flush()

    assert KnowledgeRepository(session).get(world.id, knowledge_b.id) is None
    assert MemoryRepository(session).get(world.id, memory_b.id) is None
    assert {row.id for row in KnowledgeRepository(session).list_for_world(world.id)} == {knowledge_a.id}
    assert {row.id for row in MemoryRepository(session).list_for_world(world.id)} == {memory_a.id}


def test_graph_isolation(session: Session, world: World) -> None:
    world_b = _other_world(session)
    loc_a = add_location(session, world, "Square A")
    loc_b = add_location(session, world_b, "Square B")
    add_person(session, world, "Arjun", location=loc_a)
    add_person(session, world_b, "Hidden", location=loc_b)

    graph_a = GraphService(session).build(world.id)
    labels = {node.label for node in graph_a.nodes}
    assert "Arjun" in labels
    assert "Hidden" not in labels
    assert "Square B" not in labels
    world_ids = {node.entity_id for node in graph_a.nodes if node.entity_type == "world"}
    assert world_ids == {world.id}


def test_simulation_isolation(session: Session, world: World) -> None:
    world_b = _other_world(session)
    world_b.current_minute = 480
    build_cafe_world(session, world)
    loc_b = add_location(session, world_b, "Cafe")
    person_b = add_person(
        session,
        world_b,
        "Sanjay",
        location=loc_b,
        schedule={
            "entries": [
                {
                    "time_minute": 495,
                    "action": "open_cafe",
                    "location_id": str(loc_b.id),
                }
            ]
        },
        states={"fatigue": {"level": 2}},
    )
    original_location = person_b.current_location_id
    SimulationEngine(session).advance_decision(
        world.id, PlayerDecision(action_type="WALK_TO_CAFE")
    )
    session.flush()
    session.refresh(world_b)
    session.refresh(person_b)
    assert world_b.current_minute == 480
    assert person_b.current_location_id == original_location
    assert EventRepository(session).list_for_world(world_b.id) == []
    assert (person_b.schedule or {}).get("entries")[0].get("fired") is not True
