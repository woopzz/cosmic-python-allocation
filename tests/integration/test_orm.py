import datetime as dt

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from domain import model

def test_orderline_mapper_can_load_lines(session: Session):
    sqlquery = '''
        INSERT INTO order_lines (orderid, sku, qty) VALUES
        ("order1", "RED-CHAIR", 12),
        ("order1", "RED-TABLE", 13),
        ("order2", "BLUE-LIPSTICK", 14)
    '''
    session.execute(text(sqlquery))
    assert session.query(model.OrderLine).all() == [
        model.OrderLine('order1', 'RED-CHAIR', 12),
        model.OrderLine('order1', 'RED-TABLE', 13),
        model.OrderLine('order2', 'BLUE-LIPSTICK', 14),
    ]

def test_orderline_mapper_can_save_lines(session: Session):
    new_line = model.OrderLine('order1', 'DECORATIVE-WIDGET', 12)
    session.add(new_line)
    session.commit()

    sqlquery = 'SELECT orderid, sku, qty FROM order_lines'
    rows = list(session.execute(text(sqlquery)))
    assert rows == [('order1', 'DECORATIVE-WIDGET', 12)]

def test_retrieving_batches(session: Session):
    sqlquery = '''
        INSERT INTO batches (reference, sku, _purchased_quantity, eta)
        VALUES (:reference, :sku, :purchased_qty, :eta)
    '''
    session.execute(text(sqlquery), {
        'reference': 'batch1',
        'sku': 'sku1',
        'purchased_qty': 100,
        'eta': None,
    })
    session.execute(text(sqlquery), {
        'reference': 'batch2',
        'sku': 'sku2',
        'purchased_qty': 200,
        'eta': '2011-04-11',
    })
    assert session.query(model.Batch).all() == [
        model.Batch('batch1', 'sku1', 100, eta=None),
        model.Batch('batch2', 'sku2', 200, eta=dt.date(2011, 4, 11)),
    ]

def test_saving_batches(session: Session):
    batch = model.Batch('batch1', 'sku1', 100, eta=None)
    session.add(batch)
    session.commit()

    rows = list(session.execute(text('SELECT reference, sku, _purchased_quantity, eta FROM batches')))
    assert rows == [('batch1', 'sku1', 100, None)]

def test_saving_allocation(session: Session):
    line = model.OrderLine('order1', 'sku1', 10)
    batch = model.Batch('batch1', 'sku1', 100, eta=None)
    batch.allocate(line)
    session.add(batch)
    session.commit()

    rows = list(session.execute(text('SELECT orderline_id, batch_id FROM allocations')))
    assert rows == [(line.id, batch.id)]

def test_retrieving_allocation(session: Session):
    session.execute(text('INSERT INTO order_lines (orderid, sku, qty) VALUES ("order1", "sku1", 12)'))
    [[orderline_id]] = session.execute(
        text('SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku'),
        {
            'orderid': 'order1',
            'sku': 'sku1',
        },
    )
    session.execute(text('''
        INSERT INTO batches (reference, sku, _purchased_quantity, eta)
        VALUES ("batch1", "sku1", 100, null)
    '''))
    [[batch_id]] = session.execute(
        text('SELECT id FROM batches WHERE reference=:ref AND sku=:sku'),
        {
            'ref': 'batch1',
            'sku': 'sku1',
        },
    )
    session.execute(
        text('INSERT INTO allocations (orderline_id, batch_id) VALUES (:orderline_id, :batch_id)'),
        {
            'orderline_id': orderline_id,
            'batch_id': batch_id,
        },
    )
    batch = session.query(model.Batch).one()
    assert batch._allocations == {model.OrderLine('order1', 'sku1', 12)}
