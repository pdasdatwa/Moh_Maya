from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import EntityType, RelationshipType
from app.models.natural_entity import NaturalEntity
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.business import BusinessRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository
from app.schemas.simulation import PlayerDecision
from app.simulation.engine import SimulationEngine
from tests.conftest import add_business, add_location, add_person, build_cafe_world


def test_relationship_engine_targets_event_participants(session: Session, world: World) -> None:
    fixtures = build_cafe_world(session, world)
    decoy = add_person(session, world, "Decoy")
    decoy_rel = Relationship(
        id=uuid4(),
        world_id=world.id,
        from_entity_type=EntityType.PERSON,
        from_entity_id=decoy.id,
        to_entity_type=EntityType.PERSON,
        to_entity_id=fixtures["player"].id,
        relationship_type=RelationshipType.KNOWS,
        properties={"familiarity": "stranger"},
    )
    call_rel = Relationship(
        id=uuid4(),
        world_id=world.id,
        from_entity_type=EntityType.PERSON,
        from_entity_id=fixtures["meera"].id,
        to_entity_type=EntityType.PERSON,
        to_entity_id=fixtures["sanjay"].id,
        relationship_type=RelationshipType.KNOWS,
        properties={"familiarity": "acquaintance"},
    )
    RelationshipRepository(session).add(decoy_rel)
    RelationshipRepository(session).add(call_rel)
    session.flush()

    SimulationEngine(session).advance_decision(
        world.id, PlayerDecision(action_type="WALK_TO_CAFE")
    )
    session.flush()
    session.refresh(decoy_rel)
    session.refresh(call_rel)
    assert "last_contact_day" not in (decoy_rel.properties or {})
    assert call_rel.properties["last_contact_day"] == 1
    assert call_rel.properties["last_contact_minute"] == 500


def test_economy_engine_cafe_only(session: Session, world: World) -> None:
    fixtures = build_cafe_world(session, world)
    hospital = add_location(session, world, "Hospital", "hospital")
    clinic = add_business(
        session,
        world,
        "Laketown Clinic",
        business_type="clinic",
        location=hospital,
        resources={"inventory": {"supplies": 20}},
        states={"operational": "open"},
    )
    SimulationEngine(session).advance_decision(
        world.id, PlayerDecision(action_type="WALK_TO_CAFE")
    )
    session.flush()
    cafe = BusinessRepository(session).get(world.id, fixtures["business"].id)
    loaded_clinic = BusinessRepository(session).get(world.id, clinic.id)
    assert cafe is not None
    assert loaded_clinic is not None
    assert cafe.resources["inventory"]["coffee"] == 5
    assert cafe.states.get("morning_prep_applied") is True
    assert loaded_clinic.resources["inventory"]["supplies"] == 20
    assert loaded_clinic.states.get("morning_prep_applied") is None


def test_entity_id_schedules_ignore_duplicate_names(session: Session, world: World) -> None:
    residential = add_location(session, world, "Home", "neighborhood")
    cafe_a = add_location(session, world, "Cafe", "cafe")
    cafe_b = add_location(session, world, "Cafe", "cafe")
    worker = add_person(
        session,
        world,
        "Ravi",
        location=residential,
        schedule={
            "entries": [
                {
                    "time_minute": 485,
                    "action": "go_to_work",
                    "location_id": str(cafe_b.id),
                }
            ]
        },
    )
    SimulationEngine(session).advance(world.id, 10, action_type="WAIT", time_cost_minutes=10)
    session.flush()
    loaded = PersonRepository(session).get(world.id, worker.id)
    assert loaded is not None
    assert loaded.current_location_id == cafe_b.id
    assert loaded.current_location_id != cafe_a.id


def test_energy_and_fatigue_remain_separate(session: Session, world: World) -> None:
    fixtures = build_cafe_world(session, world)
    SimulationEngine(session).advance_decision(
        world.id, PlayerDecision(action_type="WALK_TO_CAFE")
    )
    session.flush()
    player = PersonRepository(session).get(world.id, fixtures["player"].id)
    assert player is not None
    assert player.states["fatigue"]["level"] == 2
    assert player.resources["energy"]["available"] == 7
    assert "fatigue" not in player.resources
    assert "energy" not in player.states


def test_water_pressure_blocks_morning_fatigue_reduction(session: Session, world: World) -> None:
    residential = add_location(session, world, "Home")
    priya = add_person(
        session,
        world,
        "Priya",
        location=residential,
        states={"fatigue": {"level": 4}, "health": {"condition": "well"}},
        schedule={"entries": [{"time_minute": 490, "action": "morning_routine"}]},
    )
    session.add(
        NaturalEntity(
            id=uuid4(),
            world_id=world.id,
            name="Laketown Lake",
            natural_type="lake",
            location_id=residential.id,
            state={"pressure": "normal"},
            capacity_quantity={"quantity": 30, "limit": 100, "unit": "placeholder"},
        )
    )
    session.flush()
    SimulationEngine(session).advance(world.id, 15, action_type="WAIT", time_cost_minutes=15)
    session.flush()
    loaded = PersonRepository(session).get(world.id, priya.id)
    session.refresh(world)
    assert loaded is not None
    assert loaded.states["fatigue"]["level"] == 4
    assert (world.world_state.get("environmental") or {}).get("water_pressure") == "warning"
