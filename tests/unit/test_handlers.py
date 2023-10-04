import datetime as dt
from unittest import mock

import pytest

from allocation import bootstrap
from allocation.service_layer import handlers, unit_of_work
from allocation.adapters import repository
from allocation.domain import commands


class FakeRepository(repository.AbstractRepository):

    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((x for x in self._products if x.sku == sku), None)

    def _get_by_batchref(self, batchref: str):
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):

    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        publish=lambda *args: None,
    )

class TestAddBatch:

    def test_add_batch_for_new_product(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'CRUNCHY-ARMCHAIR', 100, None))
        assert bus.uow.products.get('CRUNCHY-ARMCHAIR') is not None
        assert bus.uow.committed

    def test_add_batch_for_existing_product(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'GARISH-RUG', 100, None))
        bus.handle(commands.CreateBatch('b2', 'GARISH-RUG', 99, None))
        assert 'b2' in [x.reference for x in bus.uow.products.get('GARISH-RUG').batches]


class TestAllocate:

    def test_allocates(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('batch1', 'COMPLICATED-LAMP', 100, None))
        bus.handle(commands.Allocate('o1', 'COMPLICATED-LAMP', 10))
        [batch] = bus.uow.products.get('COMPLICATED-LAMP').batches
        assert batch.available_quantity == 90

    def test_errors_for_invalid_sku(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'AREALSKU', 100, None))

        with pytest.raises(handlers.InvalidSku, match='Invalid sku NONEXISTENTSKU'):
            bus.handle(commands.Allocate('o1', 'NONEXISTENTSKU', 10))

    def test_commits(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'OMINOUS-MIRROR', 100, None))
        bus.handle(commands.Allocate('o1', 'OMINOUS-MIRROR', 10))
        assert bus.uow.committed

    def test_sends_email_on_out_of_stock_error(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'POPULAR-CURTAINS', 9, None))

        with mock.patch('allocation.adapters.email.send_mail') as mock_send_mail:
            bus.handle(commands.Allocate('o1', 'POPULAR-CURTAINS', 10))
            assert mock_send_mail.call_args == mock.call(
                f'Out of stock for POPULAR-CURTAINS',
            )


class TestChangeBatchQuantity:

    def test_changes_available_quantity(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('batch1', 'ADORABLE-SETTEE', 100, None))
        [batch] = bus.uow.products.get(sku='ADORABLE-SETTEE').batches
        assert batch.available_quantity == 100

        bus.handle(commands.ChangeBatchQuantity('batch1', 50))
        assert batch.available_quantity == 50

    def test_reallocate_if_necessary(self):
        bus = bootstrap_test_app()
        event_history = [
            commands.CreateBatch('batch1', 'INDIFFERENT-TABLE', 50, None),
            commands.CreateBatch('batch2', 'INDIFFERENT-TABLE', 50, dt.date.today()),
            commands.Allocate('order1', 'INDIFFERENT-TABLE', 20),
            commands.Allocate('order2', 'INDIFFERENT-TABLE', 20),
        ]
        for event in event_history:
            bus.handle(event)

        [batch1, batch2] = bus.uow.products.get(sku='INDIFFERENT-TABLE').batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        bus.handle(commands.ChangeBatchQuantity('batch1', 25))
        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30
