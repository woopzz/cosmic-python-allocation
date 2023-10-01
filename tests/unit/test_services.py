import pytest

from services import services
from adapters import repository
from services import unit_of_work


class FakeRepository(repository.AbstractRepository):

    def __init__(self, products):
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next((x for x in self._products if x.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):

    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'CRUNCHY-ARMCHAIR', 100, None, uow)
    assert uow.products.get('CRUNCHY-ARMCHAIR') is not None
    assert uow.committed

def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'GARISH-RUG', 100, None, uow)
    services.add_batch('b2', 'GARISH-RUG', 99, None, uow)
    assert 'b2' in [x.reference for x in uow.products.get('GARISH-RUG').batches]

def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch('batch1', 'COMPLICATED-LAMP', 100, None, uow)
    result = services.allocate('01', 'COMPLICATED-LAMP', 10, uow)
    assert result == 'batch1'

def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'AREALSKU', 100, None, uow)

    with pytest.raises(services.InvalidSku, match='Invalid sku NONEXISTENTSKU'):
        services.allocate('01', 'NONEXISTENTSKU', 10, uow)

def test_commits():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'OMINOUS-MIRROR', 100, None, uow)
    services.allocate('o1', 'OMINOUS-MIRROR', 10, uow)
    assert uow.committed is True
