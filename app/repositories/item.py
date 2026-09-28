from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item


class ItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: UUID, item_id: UUID) -> Item | None:
        return self.session.scalar(
            select(Item).where(Item.world_id == world_id, Item.id == item_id)
        )

    def list_for_world(self, world_id: UUID) -> list[Item]:
        return list(
            self.session.scalars(
                select(Item).where(Item.world_id == world_id).order_by(Item.name)
            )
        )

    def add(self, item: Item) -> Item:
        self.session.add(item)
        return item
