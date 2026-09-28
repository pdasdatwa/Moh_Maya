from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.household import Household


class HouseholdRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, household_id: UUID) -> Household | None:
        return self.session.scalar(
            select(Household).where(
                Household.world_id == world_id, Household.id == household_id
            )
        )

    def list_for_world(self, world_id: UUID) -> list[Household]:
        return list(
            self.session.scalars(
                select(Household)
                .where(Household.world_id == world_id)
                .order_by(Household.name)
            )
        )

    def add(self, household: Household) -> Household:
        self.session.add(household)
        return household
