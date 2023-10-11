import requests

from allocation import config

def post(path, json_data=None):
    if json_data is None:
        json_data = {}

    url = config.get_api_url()
    return requests.post(url + path, json=json_data)

def post_to_add_batch(ref, sku, qty, eta):
    r = post('/add_batch', json_data={'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta})
    assert r.status_code == 201

def post_to_allocate(orderid, sku, qty, expect_success=True):
    r = post('/allocate', json_data={'orderid': orderid, 'sku': sku, 'qty': qty})

    if expect_success:
        assert r.status_code == 202

    return r

def get_allocation(orderid):
    url = config.get_api_url()
    return requests.get(f'{url}/allocations/{orderid}')
