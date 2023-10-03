import datetime as dt
from unittest import mock

import pytest

from service_layer import handlers, unit_of_work, messagebus
from adapters import repository
from domain import events


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


class TestAddBatch:

    def test_add_batch_for_new_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('b1', 'CRUNCHY-ARMCHAIR', 100, None), uow)
        assert uow.products.get('CRUNCHY-ARMCHAIR') is not None
        assert uow.committed

    def test_add_batch_for_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('b1', 'GARISH-RUG', 100, None), uow)
        messagebus.handle(events.BatchCreated('b2', 'GARISH-RUG', 99, None), uow)
        assert 'b2' in [x.reference for x in uow.products.get('GARISH-RUG').batches]


class TestAllocate:

    def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('batch1', 'COMPLICATED-LAMP', 100, None), uow)
        results = messagebus.handle(events.AllocationRequired('o1', 'COMPLICATED-LAMP', 10), uow)
        assert results[0] == 'batch1'

    def test_allocate_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('b1', 'AREALSKU', 100, None), uow)

        with pytest.raises(handlers.InvalidSku, match='Invalid sku NONEXISTENTSKU'):
            messagebus.handle(events.AllocationRequired('o1', 'NONEXISTENTSKU', 10), uow)

    def test_commits(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('b1', 'OMINOUS-MIRROR', 100, None), uow)
        messagebus.handle(events.AllocationRequired('o1', 'OMINOUS-MIRROR', 10), uow)
        assert uow.committed is True

    def test_sends_email_on_out_of_stock_error(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('b1', 'POPULAR-CURTAINS', 9, None), uow)

        with mock.patch('adapters.email.send_mail') as mock_send_mail:
            messagebus.handle(events.AllocationRequired('o1', 'POPULAR-CURTAINS', 10), uow)
            assert mock_send_mail.call_args == mock.call(
                f'Out of stock for POPULAR-CURTAINS',
            )


class TestChangeBatchQuantity:

    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated('batch1', 'ADORABLE-SETTEE', 100, None), uow)
        [batch] = uow.products.get(sku='ADORABLE-SETTEE').batches
        assert batch.available_quantity == 100

        messagebus.handle(events.BatchQuantityChanged('batch1', 50), uow)
        assert batch.available_quantity == 50

    def test_reallocate_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            events.BatchCreated('batch1', 'INDIFFERENT-TABLE', 50, None),
            events.BatchCreated('batch2', 'INDIFFERENT-TABLE', 50, dt.date.today()),
            events.AllocationRequired('order1', 'INDIFFERENT-TABLE', 20),
            events.AllocationRequired('order2', 'INDIFFERENT-TABLE', 20),
        ]
        for event in event_history:
            messagebus.handle(event, uow)

        [batch1, batch2] = uow.products.get(sku='INDIFFERENT-TABLE').batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged('batch1', 25), uow)
        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30
