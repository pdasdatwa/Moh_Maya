from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.knowledge import KnowledgeRecord, Memory
from app.models.location import Location
from app.models.person import Person
from app.models.relationship import Relationship
from app.models.world import World
from app.repositories.event import EventRepository
from app.repositories.knowledge import KnowledgeRepository, MemoryRepository
from app.repositories.location import LocationRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository
from app.repositories.world import WorldRepository


class WorldNotFoundError(KeyError):
    pass


class WorldService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.worlds = WorldRepository(session)
        self.locations = LocationRepository(session)
        self.people = PersonRepository(session)
        self.events = EventRepository(session)
        self.relationships = RelationshipRepository(session)
        self.knowledge = KnowledgeRepository(session)
        self.memories = MemoryRepository(session)

    def list_worlds(self) -> list[World]:
        return self.worlds.list_all()

    def get_world(self, world_id: UUID) -> World:
        world = self.worlds.get(world_id)
        if world is None:
            raise WorldNotFoundError(f"World {world_id} not found")
        return world

    def list_locations(self, world_id: UUID) -> list[Location]:
        self.get_world(world_id)
        return self.locations.list_for_world(world_id)

    def list_people(self, world_id: UUID) -> list[Person]:
        self.get_world(world_id)
        return self.people.list_for_world(world_id)

    def list_events(self, world_id: UUID) -> list[Event]:
        self.get_world(world_id)
        return self.events.list_for_world(world_id)

    def list_relationships(self, world_id: UUID) -> list[Relationship]:
        self.get_world(world_id)
        return self.relationships.list_for_world(world_id)

    def list_knowledge(self, world_id: UUID) -> list[KnowledgeRecord]:
        self.get_world(world_id)
        return self.knowledge.list_for_world(world_id)

    def list_memories(self, world_id: UUID) -> list[Memory]:
        self.get_world(world_id)
        return self.memories.list_for_world(world_id)
