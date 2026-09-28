from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.enums import EntityType, EventOrigin, EventState, RelationshipType
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.business import BusinessRepository
from app.repositories.event import EventRepository
from app.repositories.household import HouseholdRepository
from app.repositories.location import LocationRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository
from app.repositories.world import WorldRepository
from tests.conftest import add_household, add_location, add_person


def test_world_creation(session: Session, world: World) -> None:
    loaded = WorldRepository(session).get(world.id)
    assert loaded is not None
    assert loaded.name == world.name
    assert loaded.current_day == 1
    assert loaded.current_minute == 480
    assert loaded.status == "paused"


def test_location_creation(session: Session, world: World) -> None:
    location = add_location(session, world, "Town Square", "public_square")
    loaded = LocationRepository(session).get(world.id, location.id)
    assert loaded is not None
    assert loaded.name == "Town Square"


def test_person_creation(session: Session, world: World) -> None:
    square = add_location(session, world, "Square")
    person = add_person(session, world, "Arjun", location=square)
    loaded = PersonRepository(session).get(world.id, person.id)
    assert loaded is not None
    assert loaded.current_location_id == square.id


def test_household_creation(session: Session, world: World) -> None:
    residential = add_location(session, world, "Residential Area", "neighborhood")
    household = add_household(session, world, "Sharma Household", residential)
    loaded = HouseholdRepository(session).get(world.id, household.id)
    assert loaded is not None
    assert loaded.location_id == residential.id


def test_business_creation(session: Session, world: World) -> None:
    cafe = add_location(session, world, "Cafe", "cafe")
    business = Business(
        id=uuid4(),
        world_id=world.id,
        name="Laketown Cafe",
        business_type="cafe",
        location_id=cafe.id,
        resources={"inventory": {"coffee": 5}},
        states={"operational": "closed"},
        goods_services={},
        financial_context={},
    )
    BusinessRepository(session).add(business)
    session.flush()
    loaded = BusinessRepository(session).get(world.id, business.id)
    assert loaded is not None
    assert loaded.location_id == cafe.id


def test_relationship_creation(session: Session, world: World) -> None:
    square = add_location(session, world, "Square")
    person = add_person(session, world, "Priya", location=square)
    rel = Relationship(
        id=uuid4(),
        world_id=world.id,
        from_entity_type=EntityType.PERSON,
        from_entity_id=person.id,
        to_entity_type=EntityType.LOCATION,
        to_entity_id=square.id,
        relationship_type=RelationshipType.LOCATED_AT,
        properties={},
    )
    RelationshipRepository(session).add(rel)
    session.flush()
    found = RelationshipRepository(session).find(
        world.id, EntityType.PERSON, person.id, RelationshipType.LOCATED_AT
    )
    assert found is not None
    assert found.to_entity_id == square.id


def test_event_creation(session: Session, world: World) -> None:
    square = add_location(session, world, "Square")
    event = Event(
        id=uuid4(),
        world_id=world.id,
        event_type=EventOrigin.GOD,
        specific_type="MorningBegan",
        occurred_at_day=1,
        occurred_at_minute=480,
        location_id=square.id,
        cause="test",
        state=EventState.RESOLVED,
        consequences={},
        history_record={},
    )
    EventRepository(session).add(event)
    session.flush()
    events = EventRepository(session).list_for_world(world.id)
    assert any(item.specific_type == "MorningBegan" for item in events)
