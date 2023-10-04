from sqlalchemy.sql import text

from allocation.service_layer import unit_of_work

def allocations(orderid: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        sqlquery = 'SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid'
        return [
            {'sku': sku, 'batchref': batchref}
            for sku, batchref in uow.session.execute(text(sqlquery), dict(orderid=orderid))
        ]
