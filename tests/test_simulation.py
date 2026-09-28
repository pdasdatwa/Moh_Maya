from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import ActionType, WorldStatus
from app.models.world import World
from app.repositories.event import EventRepository
from app.repositories.person import PersonRepository
from app.repositories.world import WorldRepository
from app.schemas.simulation import PlayerDecision
from app.simulation.engine import SimulationEngine
from tests.conftest import add_location, add_person, build_cafe_world


def world_locations(session: Session, world: World):
    from app.repositories.location import LocationRepository

    return LocationRepository(session).list_for_world(world.id)


def test_world_time_advancement(session: Session, world: World) -> None:
    add_location(session, world, "Cafe")
    add_person(session, world, "Arjun")
    world.player_person_id = None
    summary = SimulationEngine(session).advance(
        world.id, 10, action_type=ActionType.WAIT, time_cost_minutes=10
    )
    session.commit()
    assert world.current_minute == 490
    assert world.status == WorldStatus.PAUSED
    assert summary.started_clock == "Day 1, 08:00"
    assert summary.ended_clock == "Day 1, 08:10"


def test_simulation_advancement_walk_to_cafe(session: Session, world: World) -> None:
    fixtures = build_cafe_world(session, world)
    summary = SimulationEngine(session).advance_decision(
        world.id, PlayerDecision(action_type=ActionType.WALK_TO_CAFE)
    )
    session.commit()

    assert world.current_day == 1
    assert world.current_minute == 510
    assert world.status == WorldStatus.PAUSED
    assert summary.ticks_processed == 30
    types = {event["specific_type"] for event in summary.events}
    assert "CafeOpened" in types
    assert "PersonMorningRoutine" in types
    assert "PhoneCallReceived" in types
    assert "PersonMovedLocation" in types

    people = {person.name: person for person in PersonRepository(session).list_for_world(world.id)}
    cafe_id = fixtures["cafe"].id
    assert people["Arjun"].current_location_id == cafe_id
    assert people["Sanjay"].current_location_id == cafe_id
    assert people["Priya"].states["fatigue"]["level"] == 3
    assert people["Arjun"].states["fatigue"]["level"] == 2
    assert people["Arjun"].resources["energy"]["available"] == 7


def test_state_persistence_across_sessions(
    session: Session, world: World, session_factory
) -> None:
    add_location(session, world, "Cafe")
    add_person(session, world, "Arjun")
    world_id = world.id
    SimulationEngine(session).advance(world.id, 7, action_type=ActionType.WAIT, time_cost_minutes=7)
    session.commit()

    other = session_factory()
    try:
        reloaded = WorldRepository(other).get(world_id)
        assert reloaded is not None
        assert reloaded.current_minute == 487
        assert reloaded.status == WorldStatus.PAUSED
    finally:
        other.close()


def test_transaction_rollback_on_simulation_failure(
    session: Session, world: World, session_factory
) -> None:
    add_location(session, world, "Cafe")
    add_person(session, world, "Arjun")
    world_id = world.id
    session.commit()

    failing = session_factory()
    try:
        engine = SimulationEngine(failing, fail_after_tick=1)
        try:
            engine.advance(world_id, 5, action_type=ActionType.WAIT, time_cost_minutes=5)
            raise AssertionError("expected failure")
        except RuntimeError:
            failing.rollback()
    finally:
        failing.close()

    check = session_factory()
    try:
        reloaded = WorldRepository(check).get(world_id)
        assert reloaded is not None
        assert reloaded.current_minute == 480
        assert reloaded.status == WorldStatus.PAUSED
        assert EventRepository(check).list_for_world(world_id) == []
    finally:
        check.close()


def test_walk_to_cafe_rejects_foreign_location(session: Session, world: World) -> None:
    build_cafe_world(session, world)
    other = World(
        id=uuid4(),
        name=f"other-{uuid4()}",
        current_day=1,
        current_minute=480,
        status=WorldStatus.PAUSED,
        tick_minutes=1,
        calendar={},
        world_state={},
        history=[],
    )
    session.add(other)
    session.flush()
    foreign = add_location(session, other, "Cafe")
    try:
        SimulationEngine(session).advance_decision(
            world.id,
            PlayerDecision(action_type=ActionType.WALK_TO_CAFE, location_id=foreign.id),
        )
        raise AssertionError("expected impossible move")
    except ValueError as exc:
        assert "does not exist in this world" in str(exc)
