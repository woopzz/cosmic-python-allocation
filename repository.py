import abc

from sqlalchemy.orm import Session

import model


class AbstractRepository(abc.ABC):

    def add(self, batch: model.Batch):
        raise NotImplementedError

    def get(self, reference: str) -> model.Batch:
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
