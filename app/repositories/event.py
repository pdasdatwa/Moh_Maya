from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event, EventParticipant


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, event_id: UUID) -> Event | None:
        return self.session.scalar(
            select(Event).where(Event.world_id == world_id, Event.id == event_id)
        )

    def list_for_world(self, world_id: UUID) -> list[Event]:
        return list(
            self.session.scalars(
                select(Event)
                .where(Event.world_id == world_id)
                .order_by(Event.occurred_at_day, Event.occurred_at_minute, Event.specific_type)
            )
        )

    def add(self, event: Event) -> Event:
        self.session.add(event)
        return event

    def add_participant(self, participant: EventParticipant) -> EventParticipant:
        self.session.add(participant)
        return participant

    def list_participants(self, world_id: UUID, event_id: UUID) -> list[EventParticipant]:
        return list(
            self.session.scalars(
                select(EventParticipant).where(
                    EventParticipant.world_id == world_id,
                    EventParticipant.event_id == event_id,
                )
            )
        )
