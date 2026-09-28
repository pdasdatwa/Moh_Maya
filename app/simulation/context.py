from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from copy import deepcopy

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.business import Business
from app.models.enums import EntityType, EventOrigin, EventState, RelationshipType
from app.models.event import Event, EventParticipant
from app.models.location import Location
from app.models.person import Person
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.business import BusinessRepository
from app.repositories.event import EventRepository
from app.repositories.location import LocationRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository
from app.schemas.common import format_clock


def mutate_json(entity: object, field: str, mutator) -> None:
    data = deepcopy(getattr(entity, field) or {})
    mutator(data)
    setattr(entity, field, data)
    flag_modified(entity, field)


@dataclass
class SimulationContext:
    session: Session
    world: World
    notes: list[str] = field(default_factory=list)
    recorded_events: list[dict[str, Any]] = field(default_factory=list)
    pending_effects: list[dict[str, Any]] = field(default_factory=list)
    people: list[Person] = field(default_factory=list)
    locations: list[Location] = field(default_factory=list)
    businesses: list[Business] = field(default_factory=list)

    def load(self) -> None:
        self.people = PersonRepository(self.session).list_for_world(self.world.id)
        self.locations = LocationRepository(self.session).list_for_world(self.world.id)
        self.businesses = BusinessRepository(self.session).list_for_world(self.world.id)

    def location_by_name(self, name: str) -> Location | None:
        for location in self.locations:
            if location.name == name:
                return location
        return None

    def location_by_id(self, location_id: UUID | None) -> Location | None:
        if location_id is None:
            return None
        for location in self.locations:
            if location.id == location_id:
                return location
        return None

    def business_by_name(self, name: str) -> Business | None:
        for business in self.businesses:
            if business.name == name:
                return business
        return None

    def business_by_id(self, business_id: UUID | None) -> Business | None:
        if business_id is None:
            return None
        for business in self.businesses:
            if business.id == business_id:
                return business
        return None

    def person_by_id(self, person_id: UUID | None) -> Person | None:
        if person_id is None:
            return None
        for person in self.people:
            if person.id == person_id:
                return person
        return None

    def note(self, message: str) -> None:
        self.notes.append(message)

    def set_located_at(self, person: Person, location: Location) -> None:
        repo = RelationshipRepository(self.session)
        existing = repo.find(
            self.world.id, EntityType.PERSON, person.id, RelationshipType.LOCATED_AT
        )
        if existing:
            existing.to_entity_id = location.id
            existing.to_entity_type = EntityType.LOCATION
        else:
            repo.add(
                Relationship(
                    world_id=self.world.id,
                    from_entity_type=EntityType.PERSON,
                    from_entity_id=person.id,
                    to_entity_type=EntityType.LOCATION,
                    to_entity_id=location.id,
                    relationship_type=RelationshipType.LOCATED_AT,
                    properties={},
                )
            )

    def move_person(self, person: Person, location: Location, cause: str) -> Event:
        previous = self.location_by_id(person.current_location_id)
        person.current_location_id = location.id
        self.set_located_at(person, location)
        return self.record_event(
            event_type=EventOrigin.EMERGENT,
            specific_type="PersonMovedLocation",
            location=location,
            cause=cause,
            consequences={
                "person_id": str(person.id),
                "from_location": previous.name if previous else None,
                "to_location": location.name,
                "from_location_id": str(previous.id) if previous else None,
                "to_location_id": str(location.id),
            },
            participants=[(EntityType.PERSON, person.id, "mover")],
        )

    def record_event(
        self,
        *,
        event_type: str,
        specific_type: str,
        location: Location | None = None,
        cause: str | None = None,
        consequences: dict | None = None,
        participants: list[tuple[str, UUID, str] | None] | None = None,
    ) -> Event:
        event = Event(
            world_id=self.world.id,
            event_type=event_type,
            specific_type=specific_type,
            occurred_at_day=self.world.current_day,
            occurred_at_minute=self.world.current_minute,
            location_id=location.id if location else None,
            cause=cause,
            state=EventState.RESOLVED,
            consequences=consequences or {},
            history_record={"clock": format_clock(self.world.current_day, self.world.current_minute)},
        )
        EventRepository(self.session).add(event)
        self.session.flush()

        rel_repo = RelationshipRepository(self.session)
        participant_payload: list[dict[str, str]] = []
        for participant in participants or []:
            if participant is None:
                continue
            entity_type, entity_id, role = participant
            EventRepository(self.session).add_participant(
                EventParticipant(
                    world_id=self.world.id,
                    event_id=event.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    role=role,
                )
            )
            rel_repo.add(
                Relationship(
                    world_id=self.world.id,
                    from_entity_type=entity_type,
                    from_entity_id=entity_id,
                    to_entity_type=EntityType.EVENT,
                    to_entity_id=event.id,
                    relationship_type=RelationshipType.PARTICIPATES_IN,
                    properties={"role": role},
                )
            )
            participant_payload.append(
                {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "role": role,
                }
            )

        if location:
            rel_repo.add(
                Relationship(
                    world_id=self.world.id,
                    from_entity_type=EntityType.EVENT,
                    from_entity_id=event.id,
                    to_entity_type=EntityType.LOCATION,
                    to_entity_id=location.id,
                    relationship_type=RelationshipType.LOCATED_AT,
                    properties={},
                )
            )

        self.recorded_events.append(
            {
                "id": str(event.id),
                "specific_type": specific_type,
                "clock": format_clock(self.world.current_day, self.world.current_minute),
                "cause": cause,
                "location_id": str(location.id) if location else None,
                "participants": participant_payload,
                "consequences": consequences or {},
            }
        )
        return event
