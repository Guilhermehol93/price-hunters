"""Base Repository Class with generic CRUD operations"""

from uuid import UUID
from typing import TypeVar, Generic, Type, Optional, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        return self.db.get(self.model, id)

    def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def create(self, obj_in: ModelType) -> ModelType:
        self.db.add(obj_in)
        self.db.commit()
        self.db.refresh(obj_in)
        return obj_in

    def update(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: UUID) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
