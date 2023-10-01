import datetime as dt

from domain import model

import pytest

today = dt.date.today()
tomorrow = today + dt.timedelta(days=1)
later = today + dt.timedelta(days=10)

def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = model.Batch('in-stock-batch', 'RETRO-CLOCK', 100, eta=None)
    shipment_batch = model.Batch('shipment-batch', 'RETRO-CLOCK', 100, eta=tomorrow)
    product = model.Product(sku='RETRO-CLOCK', batches=[in_stock_batch, shipment_batch])
    line = model.OrderLine('oref', 'RETRO-CLOCK', 10)

    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100

def test_prefers_earlier_batches():
    earliest = model.Batch('speedy-batch', 'MINIMALIST-SPOON', 100, eta=today)
    medium = model.Batch('normal-batch', 'MINIMALIST-SPOON', 100, eta=tomorrow)
    latest = model.Batch('slow-batch', 'MINIMALIST-SPOON', 100, eta=later)
    product = model.Product(sku='MINIMALIST-SPOON', batches=[earliest, medium, latest])
    line = model.OrderLine('order1', 'MINIMALIST-SPOON', 10)

    product.allocate(line)

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100

def test_returns_allocated_batch_ref():
    in_stock_batch = model.Batch('in-stock-batch-ref', 'HIGHBROW-POSTER', 100, eta=None)
    shipment_batch = model.Batch('shipment-batch-ref', 'HIGHBROW-POSTER', 100, eta=tomorrow)
    product = model.Product(sku='HIGHBROW-POSTER', batches=[in_stock_batch, shipment_batch])
    line = model.OrderLine('oref', 'HIGHBROW-POSTER', 10)

    allocation = product.allocate(line)
    assert allocation == in_stock_batch.reference

def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = model.Batch('batch1', 'SMALL-FORK', 10, eta=today)
    product = model.Product(sku='SMALL-FORK', batches=[batch])

    product.allocate(model.OrderLine('order1', 'SMALL-FORK', 10))

    with pytest.raises(model.OutOfStock, match='SMALL-FORK'):
        product.allocate(model.OrderLine('order2', 'SMALL-FORK', 1))

def test_increments_version_number():
    batch = model.Batch('b1', 'SCANDI-PEN', 100, eta=None)
    product = model.Product(sku='SCANDI-PEN', batches=[batch])
    line = model.OrderLine('oref', 'SCANDI-PEN', 10)

    product.version_number = 7
    product.allocate(line)

    assert product.version_number == 8
