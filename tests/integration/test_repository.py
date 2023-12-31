import pytest

from allocation.domain import model
from allocation.adapters import repository

@pytest.mark.usefixtures('mappers')
def test_get_by_batchref(sqlite_session_factory):
    repo = repository.SqlAlchemyRepository(sqlite_session_factory())
    b1 = model.Batch(ref='b1', sku='sku1', qty=100, eta=None)
    b2 = model.Batch(ref='b2', sku='sku1', qty=100, eta=None)
    b3 = model.Batch(ref='b3', sku='sku2', qty=100, eta=None)
    p1 = model.Product(sku='sku1', batches=[b1, b2])
    p2 = model.Product(sku='sku2', batches=[b3])
    repo.add(p1)
    repo.add(p2)
    assert repo.get_by_batchref('b2') == p1
    assert repo.get_by_batchref('b3') == p2
