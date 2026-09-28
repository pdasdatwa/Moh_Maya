from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.world import World
from app.models.enums import WorldStatus
from sqlalchemy.engine import make_url


def test_database_connection(session: Session) -> None:
    result = session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_test_database_is_not_mohmaya(session: Session) -> None:
    name = session.execute(text("SELECT current_database()")).scalar()
    assert name == "mohmaya_test"
    settings = get_settings()
    assert make_url(settings.test_database_url).database == "mohmaya_test"
    assert make_url(settings.database_url).database == "mohmaya"
    assert make_url(settings.test_database_url).database != make_url(settings.database_url).database


def test_player_person_id_fk_rejects_unknown_person(session: Session) -> None:
    world = World(
        id=uuid4(),
        name=f"fk-world-{uuid4()}",
        current_day=1,
        current_minute=480,
        status=WorldStatus.PAUSED,
        tick_minutes=1,
        calendar={},
        world_state={},
        history=[],
        player_person_id=uuid4(),
    )
    session.add(world)
    with pytest.raises(IntegrityError):
        session.flush()
