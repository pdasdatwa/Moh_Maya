from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.person import Person


class PersonRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, person_id: UUID) -> Person | None:
        return self.session.scalar(
            select(Person).where(Person.world_id == world_id, Person.id == person_id)
        )

    def get_by_name(self, world_id: UUID, name: str) -> Person | None:
        return self.session.scalar(
            select(Person).where(Person.world_id == world_id, Person.name == name)
        )

    def list_for_world(self, world_id: UUID) -> list[Person]:
        return list(
            self.session.scalars(
                select(Person).where(Person.world_id == world_id).order_by(Person.name)
            )
        )

    def add(self, person: Person) -> Person:
        self.session.add(person)
        return person
