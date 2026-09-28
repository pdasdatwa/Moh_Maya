"""Seed the Laketown development world."""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.business import Business
from app.models.enums import (
    EntityType,
    EventOrigin,
    EventState,
    KnowledgeKind,
    KnowledgeLayer,
    RelationshipType,
    WorldStatus,
)
from app.models.event import Event, EventParticipant
from app.models.household import Household
from app.models.infrastructure import Infrastructure
from app.models.item import Item
from app.models.knowledge import KnowledgeRecord, Memory
from app.models.location import Location
from app.models.natural_entity import NaturalEntity
from app.models.organization import Organization
from app.models.person import Person
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.world import WorldRepository
from app.schemas.common import format_clock

LAKETOWN = "Laketown"
DAY = 1
MINUTE = 480  # 08:00


def _rel(
    session: Session,
    world_id: UUID,
    relationship_type: str,
    from_type: str,
    from_id: UUID,
    to_type: str,
    to_id: UUID,
    properties: dict | None = None,
) -> Relationship:
    rel = Relationship(
        id=uuid4(),
        world_id=world_id,
        from_entity_type=from_type,
        from_entity_id=from_id,
        to_entity_type=to_type,
        to_entity_id=to_id,
        relationship_type=relationship_type,
        properties=properties or {},
    )
    session.add(rel)
    return rel


def seed_laketown(session: Session, reset: bool = False) -> World:
    repo = WorldRepository(session)
    existing = repo.get_by_name(LAKETOWN)
    if existing and not reset:
        print(f"Laketown already exists: {existing.id}")
        return existing
    if existing and reset:
        session.delete(existing)
        session.flush()

    world = World(
        id=uuid4(),
        name=LAKETOWN,
        current_day=DAY,
        current_minute=MINUTE,
        status=WorldStatus.PAUSED,
        tick_minutes=1,
        calendar={"system": "placeholder", "start_year": 2035},
        world_state={
            "environmental": {"weather": "clear"},
            "economic": {"condition": "stable"},
            "social": {"condition": "calm"},
        },
        history=[{"year": 2032, "fact": "A flood reached the lakeshore."}],
    )
    session.add(world)
    session.flush()

    town_square = Location(
        id=uuid4(),
        world_id=world.id,
        name="Town Square",
        location_type="public_square",
        parent_location_id=None,
        state={"crowd": "quiet"},
        capacity={"people": 80},
        properties={"public": True},
    )
    cafe = Location(
        id=uuid4(),
        world_id=world.id,
        name="Cafe",
        location_type="cafe",
        parent_location_id=town_square.id,
        state={"operational": "closed"},
        capacity={"people": 24, "seats": 16},
        properties={"opens_at_minute": 495},
    )
    hospital = Location(
        id=uuid4(),
        world_id=world.id,
        name="Hospital",
        location_type="hospital",
        parent_location_id=town_square.id,
        state={"operational": "open"},
        capacity={"beds": 12},
        properties={},
    )
    residential = Location(
        id=uuid4(),
        world_id=world.id,
        name="Residential Area",
        location_type="neighborhood",
        parent_location_id=town_square.id,
        state={"quiet": True},
        capacity={"households": 20},
        properties={},
    )
    session.add_all([town_square, cafe, hospital, residential])
    session.flush()
    world_state = dict(world.world_state or {})
    world_state["demo"] = {"walk_to_cafe_location_id": str(cafe.id)}
    world.world_state = world_state

    sharma = Household(
        id=uuid4(),
        world_id=world.id,
        name="Sharma Household",
        location_id=residential.id,
        resources={"money": {"amount": 4200}, "food": {"days": 5}},
        states={"economic": {"condition": "stable"}},
        obligations={"rent_due_day": 30},
        history=[],
    )
    kumar = Household(
        id=uuid4(),
        world_id=world.id,
        name="Kumar Household",
        location_id=residential.id,
        resources={"money": {"amount": 2800}, "food": {"days": 4}},
        states={"economic": {"condition": "tight"}},
        obligations={"rent_due_day": 30},
        history=[],
    )
    arjun_home = Household(
        id=uuid4(),
        world_id=world.id,
        name="Arjun Household",
        location_id=residential.id,
        resources={"money": {"amount": 1600}, "food": {"days": 3}},
        states={"economic": {"condition": "starting_out"}},
        obligations={"rent_due_day": 30},
        history=[],
    )
    session.add_all([sharma, kumar, arjun_home])
    session.flush()

    council = Organization(
        id=uuid4(),
        world_id=world.id,
        name="Laketown Municipal Council",
        org_type="government",
        resources={"budget": {"amount": 50000}},
        states={"institutional": {"condition": "functioning"}},
        roles={"mayor": "unassigned"},
    )
    session.add(council)
    session.flush()

    cafe_biz = Business(
        id=uuid4(),
        world_id=world.id,
        name="Laketown Cafe",
        business_type="cafe",
        location_id=cafe.id,
        organization_id=None,
        resources={"money": {"amount": 2400}, "inventory": {"coffee": 12, "milk": 8}},
        states={"operational": "closed", "economic": {"condition": "stable"}},
        goods_services={"menu": ["tea", "coffee", "breakfast"]},
        financial_context={"prices": {"coffee": 40}},
    )
    clinic = Business(
        id=uuid4(),
        world_id=world.id,
        name="Laketown Clinic",
        business_type="clinic",
        location_id=hospital.id,
        organization_id=council.id,
        resources={"money": {"amount": 9000}, "inventory": {"supplies": 20}},
        states={"operational": "open", "economic": {"condition": "stable"}},
        goods_services={"services": ["consultation", "first_aid"]},
        financial_context={"prices": {"consultation": 200}},
    )
    session.add_all([cafe_biz, clinic])
    session.flush()

    water = Infrastructure(
        id=uuid4(),
        world_id=world.id,
        name="Municipal Water Works",
        infra_type="water",
        location_id=town_square.id,
        capacity={"limit": 100},
        state={"used": 40, "pressure": "normal"},
        resources={"water": {"category": "Water"}},
        dependencies={"source": "Laketown Lake"},
    )
    lake = NaturalEntity(
        id=uuid4(),
        world_id=world.id,
        name="Laketown Lake",
        natural_type="lake",
        location_id=town_square.id,
        state={"pressure": "normal"},
        capacity_quantity={"quantity": 80, "limit": 100, "unit": "placeholder"},
    )
    session.add_all([water, lake])
    session.flush()

    def person(**kwargs) -> Person:
        created = Person(id=uuid4(), world_id=world.id, **kwargs)
        session.add(created)
        return created

    default_states = {
        "health": {"condition": "well"},
        "hunger": {"level": 1},
        "fatigue": {"level": 2},
        "stress": {"level": 1},
        "mood": {"label": "neutral"},
    }

    arjun = person(
        name="Arjun",
        age=28,
        current_location_id=town_square.id,
        household_id=arjun_home.id,
        attributes={"personality": {"placeholder": True}},
        states=deepcopy(default_states),
        resources={"money": {"amount": 900}, "energy": {"available": 8}},
        roles={"profession": "newcomer", "is_player": True},
        goals={"today": "visit the cafe"},
        circumstances={"just_arrived": True},
        history=["Moved to Laketown recently."],
        schedule={"entries": []},
    )
    sanjay = person(
        name="Sanjay",
        age=43,
        current_location_id=residential.id,
        household_id=sharma.id,
        attributes={"personality": {"placeholder": True}},
        states=deepcopy(default_states),
        resources={"money": {"amount": 3100}, "energy": {"available": 7}},
        roles={"profession": "cafe_owner"},
        goals={"today": "open the cafe"},
        circumstances={"owns_cafe": True},
        history=["Left IT after 14 years and opened the cafe."],
        schedule={
            "entries": [
                {
                    "time_minute": 495,
                    "action": "open_cafe",
                    "location_id": str(cafe.id),
                    "business_id": str(cafe_biz.id),
                }
            ]
        },
    )
    priya = person(
        name="Priya",
        age=36,
        current_location_id=residential.id,
        household_id=sharma.id,
        attributes={"personality": {"placeholder": True}},
        states={**deepcopy(default_states), "fatigue": {"level": 3}},
        resources={"money": {"amount": 1500}, "energy": {"available": 6}},
        roles={"profession": "teacher"},
        goals={"today": "morning routine then prepare for school"},
        circumstances={"lives_with_brother": True},
        history=["Teaches at the town school."],
        schedule={"entries": [{"time_minute": 490, "action": "morning_routine"}]},
    )
    ravi = person(
        name="Ravi",
        age=40,
        current_location_id=residential.id,
        household_id=kumar.id,
        attributes={"personality": {"placeholder": True}},
        states={**deepcopy(default_states), "stress": {"level": 3}},
        resources={"money": {"amount": 800}, "energy": {"available": 7}},
        roles={"profession": "clinic_clerk"},
        goals={"today": "get to work on time"},
        circumstances={"worried_about_home": True},
        history=["Works the front desk at the clinic."],
        schedule={
            "entries": [
                {
                    "time_minute": 540,
                    "action": "go_to_work",
                    "location_id": str(hospital.id),
                }
            ]
        },
    )
    meera = person(
        name="Meera",
        age=32,
        current_location_id=residential.id,
        household_id=sharma.id,
        attributes={"personality": {"placeholder": True}},
        states=deepcopy(default_states),
        resources={"money": {"amount": 1100}, "energy": {"available": 8}},
        roles={"profession": "journalist"},
        goals={"today": "return follow-up calls"},
        circumstances={"waiting_for_a_call": True},
        history=["Writes for the local paper."],
        schedule={
            "entries": [
                {
                    "time_minute": 500,
                    "action": "receive_call",
                    "other_person_id": str(sanjay.id),
                }
            ]
        },
    )
    asha = person(
        name="Asha",
        age=38,
        current_location_id=residential.id,
        household_id=kumar.id,
        attributes={"personality": {"placeholder": True}},
        states={**deepcopy(default_states), "mood": {"label": "unhappy"}, "stress": {"level": 4}},
        resources={"money": {"amount": 600}, "energy": {"available": 5}},
        roles={"profession": "shop_assistant"},
        goals={"today": "think about the future"},
        circumstances={"considering_leaving": True},
        history=["Married to Ravi."],
        schedule={"entries": []},
    )
    nandini = person(
        name="Dr. Nandini",
        age=45,
        current_location_id=hospital.id,
        household_id=None,
        attributes={"personality": {"placeholder": True}},
        states=deepcopy(default_states),
        resources={"money": {"amount": 5400}, "energy": {"available": 7}},
        roles={"profession": "doctor"},
        goals={"today": "morning clinic hours"},
        circumstances={"on_duty": True},
        history=["Runs the town clinic."],
        schedule={"entries": []},
    )
    vikram = person(
        name="Vikram",
        age=50,
        current_location_id=residential.id,
        household_id=None,
        attributes={"personality": {"placeholder": True}},
        states=deepcopy(default_states),
        resources={"money": {"amount": 2200}, "energy": {"available": 6}},
        roles={"profession": "retired"},
        goals={"today": "walk later"},
        circumstances={"neighbor": True},
        history=["Has lived in Laketown for decades."],
        schedule={"entries": []},
    )
    session.flush()
    world.player_person_id = arjun.id

    keys = Item(
        id=uuid4(),
        world_id=world.id,
        name="Cafe Keys",
        item_type="keys",
        description="Keys to Laketown Cafe",
        owner_entity_type=EntityType.PERSON,
        owner_entity_id=sanjay.id,
        location_id=residential.id,
        condition={"wear": "used"},
        state={},
        value={"price": 0},
        properties={},
    )
    phone = Item(
        id=uuid4(),
        world_id=world.id,
        name="Arjun's Phone",
        item_type="phone",
        description="A personal phone",
        owner_entity_type=EntityType.PERSON,
        owner_entity_id=arjun.id,
        location_id=town_square.id,
        condition={"wear": "good"},
        state={},
        value={"price": 400},
        properties={},
    )
    session.add_all([keys, phone])
    session.flush()

    morning = Event(
        id=uuid4(),
        world_id=world.id,
        event_type=EventOrigin.GOD,
        specific_type="MorningBegan",
        occurred_at_day=DAY,
        occurred_at_minute=MINUTE,
        location_id=town_square.id,
        cause="World seed",
        state=EventState.RESOLVED,
        consequences={"status": "world_ready"},
        history_record={"clock": format_clock(DAY, MINUTE)},
    )
    session.add(morning)
    session.flush()
    session.add(
        EventParticipant(
            id=uuid4(),
            world_id=world.id,
            event_id=morning.id,
            entity_type=EntityType.PERSON,
            entity_id=arjun.id,
            role="observer",
        )
    )

    for location in (town_square, cafe, hospital, residential):
        _rel(session, world.id, RelationshipType.CONTAINS, EntityType.WORLD, world.id, EntityType.LOCATION, location.id)
    _rel(session, world.id, RelationshipType.CONTAINS, EntityType.LOCATION, town_square.id, EntityType.LOCATION, cafe.id)
    _rel(session, world.id, RelationshipType.CONTAINS, EntityType.LOCATION, town_square.id, EntityType.LOCATION, hospital.id)
    _rel(session, world.id, RelationshipType.CONTAINS, EntityType.LOCATION, town_square.id, EntityType.LOCATION, residential.id)
    _rel(session, world.id, RelationshipType.LOCATED_IN, EntityType.LOCATION, cafe.id, EntityType.LOCATION, town_square.id)
    _rel(session, world.id, RelationshipType.LOCATED_IN, EntityType.LOCATION, hospital.id, EntityType.LOCATION, town_square.id)
    _rel(session, world.id, RelationshipType.LOCATED_IN, EntityType.LOCATION, residential.id, EntityType.LOCATION, town_square.id)
    _rel(session, world.id, RelationshipType.LOCATED_AT, EntityType.BUSINESS, cafe_biz.id, EntityType.LOCATION, cafe.id)
    _rel(session, world.id, RelationshipType.LOCATED_AT, EntityType.BUSINESS, clinic.id, EntityType.LOCATION, hospital.id)

    placements = [
        (arjun, town_square),
        (sanjay, residential),
        (priya, residential),
        (ravi, residential),
        (meera, residential),
        (asha, residential),
        (nandini, hospital),
        (vikram, residential),
    ]
    for person_row, location in placements:
        _rel(
            session,
            world.id,
            RelationshipType.LOCATED_AT,
            EntityType.PERSON,
            person_row.id,
            EntityType.LOCATION,
            location.id,
        )

    for member, household in (
        (arjun, arjun_home),
        (sanjay, sharma),
        (priya, sharma),
        (meera, sharma),
        (ravi, kumar),
        (asha, kumar),
    ):
        _rel(session, world.id, RelationshipType.LIVES_IN, EntityType.PERSON, member.id, EntityType.HOUSEHOLD, household.id)
        _rel(session, world.id, RelationshipType.MEMBER_OF, EntityType.PERSON, member.id, EntityType.HOUSEHOLD, household.id)

    _rel(session, world.id, RelationshipType.WORKS_AT, EntityType.PERSON, sanjay.id, EntityType.BUSINESS, cafe_biz.id)
    _rel(session, world.id, RelationshipType.OWNS, EntityType.PERSON, sanjay.id, EntityType.BUSINESS, cafe_biz.id)
    _rel(session, world.id, RelationshipType.WORKS_AT, EntityType.PERSON, nandini.id, EntityType.BUSINESS, clinic.id)
    _rel(session, world.id, RelationshipType.WORKS_AT, EntityType.PERSON, ravi.id, EntityType.BUSINESS, clinic.id)
    _rel(session, world.id, RelationshipType.MEMBER_OF, EntityType.PERSON, nandini.id, EntityType.ORGANIZATION, council.id)
    _rel(
        session,
        world.id,
        RelationshipType.RELATED_TO,
        EntityType.PERSON,
        sanjay.id,
        EntityType.PERSON,
        priya.id,
        {"kind": "siblings"},
    )
    _rel(
        session,
        world.id,
        RelationshipType.RELATED_TO,
        EntityType.PERSON,
        ravi.id,
        EntityType.PERSON,
        asha.id,
        {"kind": "married", "affection": "strained"},
    )
    _rel(
        session,
        world.id,
        RelationshipType.KNOWS,
        EntityType.PERSON,
        ravi.id,
        EntityType.PERSON,
        asha.id,
        {"familiarity": "deep"},
    )
    _rel(
        session,
        world.id,
        RelationshipType.KNOWS,
        EntityType.PERSON,
        meera.id,
        EntityType.PERSON,
        sanjay.id,
        {"familiarity": "acquaintance"},
    )
    _rel(session, world.id, RelationshipType.OWNS, EntityType.PERSON, sanjay.id, EntityType.ITEM, keys.id)
    _rel(session, world.id, RelationshipType.OWNS, EntityType.PERSON, arjun.id, EntityType.ITEM, phone.id)
    _rel(session, world.id, RelationshipType.DEPENDS_ON, EntityType.INFRASTRUCTURE, water.id, EntityType.NATURAL_ENTITY, lake.id)
    _rel(session, world.id, RelationshipType.SERVES, EntityType.INFRASTRUCTURE, water.id, EntityType.LOCATION, town_square.id)
    _rel(session, world.id, RelationshipType.LOCATED_IN, EntityType.NATURAL_ENTITY, lake.id, EntityType.LOCATION, town_square.id)
    _rel(
        session,
        world.id,
        RelationshipType.PARTICIPATES_IN,
        EntityType.PERSON,
        arjun.id,
        EntityType.EVENT,
        morning.id,
        {"role": "observer"},
    )
    _rel(
        session,
        world.id,
        RelationshipType.LOCATED_AT,
        EntityType.EVENT,
        morning.id,
        EntityType.LOCATION,
        town_square.id,
    )

    session.add_all(
        [
            KnowledgeRecord(
                id=uuid4(),
                world_id=world.id,
                person_id=None,
                subject_entity_type=EntityType.PERSON,
                subject_entity_id=asha.id,
                content="Asha is considering leaving Ravi.",
                knowledge_kind=KnowledgeKind.FACT,
                layer=KnowledgeLayer.WORLD_TRUTH,
                is_correct=True,
                source="world_authoritative",
                established_at_day=DAY,
                established_at_minute=MINUTE,
                details={},
            ),
            KnowledgeRecord(
                id=uuid4(),
                world_id=world.id,
                person_id=ravi.id,
                subject_entity_type=EntityType.PERSON,
                subject_entity_id=asha.id,
                content="Asha is unhappy.",
                knowledge_kind=KnowledgeKind.BELIEF,
                layer=KnowledgeLayer.PERSON,
                is_correct=True,
                source="observation",
                established_at_day=DAY,
                established_at_minute=MINUTE,
                details={},
            ),
            KnowledgeRecord(
                id=uuid4(),
                world_id=world.id,
                person_id=arjun.id,
                subject_entity_type=EntityType.PERSON,
                subject_entity_id=sanjay.id,
                content="There is a cafe in town.",
                knowledge_kind=KnowledgeKind.FACT,
                layer=KnowledgeLayer.PLAYER,
                is_correct=True,
                source="arrival",
                established_at_day=DAY,
                established_at_minute=MINUTE,
                details={},
            ),
            Memory(
                id=uuid4(),
                world_id=world.id,
                person_id=sanjay.id,
                content="I left IT and opened this cafe.",
                related_event_id=None,
                occurred_at_day=DAY,
                occurred_at_minute=MINUTE,
                salience={"placeholder": True},
            ),
        ]
    )

    session.commit()
    session.refresh(world)
    print(
        f"Seeded {LAKETOWN} id={world.id} time={format_clock(world.current_day, world.current_minute)} status={world.status}"
    )
    return world


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Laketown development world")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate Laketown")
    args = parser.parse_args()
    session = SessionLocal()
    try:
        seed_laketown(session, reset=args.reset)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
