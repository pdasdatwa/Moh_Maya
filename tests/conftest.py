from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import db_session
from app.core.config import get_settings
from app.core.database import get_db
from app.main import app

get_settings.cache_clear()
from app.models.business import Business
from app.models.enums import WorldStatus
from app.models.household import Household
from app.models.location import Location
from app.models.person import Person
from app.models.world import World

ROOT = Path(__file__).resolve().parent.parent


def _ensure_test_database(test_url: str) -> None:
    parsed = make_url(test_url)
    if parsed.database != "mohmaya_test":
        raise RuntimeError(
            f"pytest must use mohmaya_test, got database {parsed.database!r}"
        )
    admin_engine = create_engine(
        parsed.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'mohmaya_test'")
            ).scalar()
            if not exists:
                conn.execute(text("CREATE DATABASE mohmaya_test"))
    finally:
        admin_engine.dispose()


def _upgrade_test_database(test_url: str) -> None:
    alembic_cfg = Config(str(ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", test_url)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    settings = get_settings()
    test_url = settings.test_database_url
    parsed = make_url(test_url)
    if parsed.database != "mohmaya_test":
        raise RuntimeError("TEST_DATABASE_URL must point at mohmaya_test")
    if parsed.database == make_url(settings.database_url).database:
        raise RuntimeError("pytest must not use DATABASE_URL / the development database")

    _ensure_test_database(test_url)
    import os

    os.environ["ALEMBIC_DATABASE_URL"] = test_url
    _upgrade_test_database(test_url)
    engine = create_engine(test_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def session_factory(test_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False, class_=Session)


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    db = session_factory()
    try:
        yield db
    finally:
        db.rollback()
        for world in db.scalars(select(World)).all():
            world.player_person_id = None
        db.flush()
        for world in db.scalars(select(World)).all():
            db.delete(world)
        db.commit()
        db.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def world(session: Session) -> World:
    created = World(
        id=uuid4(),
        name=f"test-world-{uuid4()}",
        current_day=1,
        current_minute=480,
        status=WorldStatus.PAUSED,
        tick_minutes=1,
        calendar={},
        world_state={"environmental": {"weather": "clear"}},
        history=[],
    )
    session.add(created)
    session.flush()
    return created


def add_location(session: Session, world: World, name: str, location_type: str = "place") -> Location:
    location = Location(
        id=uuid4(),
        world_id=world.id,
        name=name,
        location_type=location_type,
        state={},
        capacity={},
        properties={},
    )
    session.add(location)
    session.flush()
    return location


def add_household(session: Session, world: World, name: str, location: Location | None = None) -> Household:
    household = Household(
        id=uuid4(),
        world_id=world.id,
        name=name,
        location_id=location.id if location else None,
        resources={},
        states={},
        obligations={},
        history=[],
    )
    session.add(household)
    session.flush()
    return household


def add_business(
    session: Session,
    world: World,
    name: str,
    *,
    business_type: str = "cafe",
    location: Location | None = None,
    resources: dict | None = None,
    states: dict | None = None,
) -> Business:
    business = Business(
        id=uuid4(),
        world_id=world.id,
        name=name,
        business_type=business_type,
        location_id=location.id if location else None,
        resources=resources or {},
        states=states or {"operational": "closed"},
        goods_services={},
        financial_context={},
    )
    session.add(business)
    session.flush()
    return business


def add_person(
    session: Session,
    world: World,
    name: str,
    location: Location | None = None,
    household: Household | None = None,
    **kwargs,
) -> Person:
    person = Person(
        id=uuid4(),
        world_id=world.id,
        name=name,
        age=kwargs.pop("age", 30),
        current_location_id=location.id if location else None,
        household_id=household.id if household else None,
        attributes=kwargs.pop("attributes", {}),
        states=kwargs.pop("states", {"fatigue": {"level": 2}, "health": {"condition": "well"}}),
        resources=kwargs.pop("resources", {"money": {"amount": 100}, "energy": {"available": 8}}),
        roles=kwargs.pop("roles", {}),
        goals=kwargs.pop("goals", {}),
        circumstances=kwargs.pop("circumstances", {}),
        history=kwargs.pop("history", []),
        schedule=kwargs.pop("schedule", {"entries": []}),
    )
    session.add(person)
    session.flush()
    return person


def build_cafe_world(session: Session, world: World) -> dict:
    cafe = add_location(session, world, "Cafe", "cafe")
    residential = add_location(session, world, "Residential Area", "neighborhood")
    business = add_business(
        session,
        world,
        "Laketown Cafe",
        business_type="cafe",
        location=cafe,
        resources={"inventory": {"coffee": 6}},
        states={"operational": "closed"},
    )
    player = add_person(
        session,
        world,
        "Arjun",
        location=residential,
        states={"fatigue": {"level": 1}, "health": {"condition": "well"}},
        resources={"money": {"amount": 100}, "energy": {"available": 8}},
    )
    sanjay = add_person(
        session,
        world,
        "Sanjay",
        location=residential,
        schedule={
            "entries": [
                {
                    "time_minute": 495,
                    "action": "open_cafe",
                    "location_id": str(cafe.id),
                    "business_id": str(business.id),
                }
            ]
        },
    )
    priya = add_person(
        session,
        world,
        "Priya",
        location=residential,
        states={"fatigue": {"level": 4}, "health": {"condition": "well"}},
        schedule={"entries": [{"time_minute": 490, "action": "morning_routine"}]},
    )
    meera = add_person(
        session,
        world,
        "Meera",
        location=residential,
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
    world.player_person_id = player.id
    world_state = dict(world.world_state or {})
    world_state["demo"] = {"walk_to_cafe_location_id": str(cafe.id)}
    world.world_state = world_state
    session.flush()
    return {
        "cafe": cafe,
        "residential": residential,
        "business": business,
        "player": player,
        "sanjay": sanjay,
        "priya": priya,
        "meera": meera,
    }
