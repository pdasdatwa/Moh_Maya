from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import ActionType, KnowledgeKind, KnowledgeLayer
from app.models.knowledge import KnowledgeRecord, Memory
from app.models.world import World
from tests.conftest import build_cafe_world


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_worlds_god_endpoint(client: TestClient, world: World) -> None:
    response = client.get("/worlds")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert str(world.id) in ids


def test_advance_walk_to_cafe_http(client: TestClient, session: Session, world: World) -> None:
    fixtures = build_cafe_world(session, world)
    response = client.post(
        f"/world/{world.id}/simulation/advance",
        json={
            "action_type": ActionType.WALK_TO_CAFE,
            "location_id": str(fixtures["cafe"].id),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["started_clock"] == "Day 1, 08:00"
    assert body["ended_clock"] == "Day 1, 08:30"
    assert body["status"] == "paused"
    types = {event["specific_type"] for event in body["events"]}
    assert "CafeOpened" in types
    assert "PhoneCallReceived" in types


def test_advance_missing_world_returns_404(client: TestClient) -> None:
    response = client.post(
        f"/world/{uuid4()}/simulation/advance",
        json={"action_type": "WAIT", "minutes": 1},
    )
    assert response.status_code == 404


def test_knowledge_and_memories_god_endpoints(
    client: TestClient, session: Session, world: World
) -> None:
    from tests.conftest import add_person

    person = add_person(session, world, "Meera")
    session.add(
        KnowledgeRecord(
            id=uuid4(),
            world_id=world.id,
            person_id=person.id,
            content="A test fact",
            knowledge_kind=KnowledgeKind.FACT,
            layer=KnowledgeLayer.PERSON,
            is_correct=True,
            source="test",
            established_at_day=1,
            established_at_minute=480,
            details={},
        )
    )
    session.add(
        Memory(
            id=uuid4(),
            world_id=world.id,
            person_id=person.id,
            content="A test memory",
            related_event_id=None,
            occurred_at_day=1,
            occurred_at_minute=480,
            salience={},
        )
    )
    session.flush()

    knowledge = client.get(f"/world/{world.id}/knowledge")
    memories = client.get(f"/world/{world.id}/memories")
    assert knowledge.status_code == 200
    assert memories.status_code == 200
    assert any(item["content"] == "A test fact" for item in knowledge.json())
    assert any(item["content"] == "A test memory" for item in memories.json())
    missing = client.get(f"/world/{uuid4()}/knowledge")
    assert missing.status_code == 404
