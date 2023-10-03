import json
import logging

import pytest
from tenacity import Retrying, stop_after_delay

from . import api_client, redis_client
from ..random_refs import random_orderid, random_sku, random_batchref

@pytest.mark.usefixtures('postgres_db')
@pytest.mark.usefixtures('restart_api')
@pytest.mark.usefixtures('restart_redis_pubsub')
def test_change_batch_quantity_leading_to_reallocation():
    print('---------')
    print('---------')
    print('---------')
    print('---------')
    print('---------')
    print('---------')
    print('---------')
    print('---------')
    print('---------')
    logging.info('WJKFLJSLKFJSLKFJLKDS')
    orderid, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref('old'), random_batchref('newer')
    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02')
    api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-02')

    response = api_client.post_to_allocate(orderid, sku, 10)
    assert response.json()['batchref'] == earlier_batch

    subscription = redis_client.subscribe_to('line_allocated')
    redis_client.publish_message('change_batch_quantity', {
        'batchref': earlier_batch, 'qty': 5,
    })

    messages = []
    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = subscription.get_message(timeout=1)
            if message:
                messages.append(message)
            data = json.loads(messages[-1]['data'])
            assert data['orderid'] == orderid
            assert data['batchref'] == later_batch
