import datetime as dt

from flask import Flask, request, jsonify

from allocation import views, bootstrap
from allocation.service_layer import handlers
from allocation.domain import commands
from . import validation

app = Flask(__name__)
app.register_error_handler(validation.ValidationError, validation.handle_invalid_command)

bus = bootstrap.bootstrap()

@app.route('/add_batch', methods=['POST'])
def add_batch():
    add_batch_request = validation.AddBatch(**request.json)
    bus.handle(commands.CreateBatch(
        ref=add_batch_request.ref,
        sku=add_batch_request.sku,
        qty=add_batch_request.qty,
        eta=add_batch_request.eta,
    ))
    return 'OK', 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    allocation_request = validation.Allocation(**request.json)

    try:
        bus.handle(commands.Allocate(
            orderid=allocation_request.orderid,
            sku=allocation_request.sku,
            qty=allocation_request.qty,
        ))
        return 'OK', 202
    except handlers.InvalidSku as exc:
        return {'message': str(exc)}, 400

@app.route('/allocations/<orderid>', methods=['GET'])
def allocations_view_endpoint(orderid):
    result = views.allocations(orderid, bus.uow)
    if not result:
        return 'Not found', 404
    return jsonify(result), 200
