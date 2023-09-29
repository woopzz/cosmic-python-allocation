import abc
from typing import List

from sqlalchemy.orm import Session

from domain import model


class AbstractRepository(abc.ABC):

    def add(self, batch: model.Batch):
        raise NotImplementedError

    def get(self, reference: str) -> model.Batch:
        raise NotImplementedError

    def list(self) -> List[model.Batch]:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session: Session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()
