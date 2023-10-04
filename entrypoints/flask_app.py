import datetime as dt

from flask import Flask, request, jsonify

import views
import bootstrap
from service_layer import handlers
from domain import commands

app = Flask(__name__)
bus = bootstrap.bootstrap()

@app.route('/add_batch', methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = dt.datetime.fromisoformat(eta).date()

    bus.handle(commands.CreateBatch(request.json['ref'], request.json['sku'], request.json['qty'], eta))
    return 'OK', 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    try:
        bus.handle(commands.Allocate(request.json['orderid'], request.json['sku'], request.json['qty']))
        return 'OK', 202
    except handlers.InvalidSku as exc:
        return {'message': str(exc)}, 400

@app.route('/allocations/<orderid>', methods=['GET'])
def allocations_view_endpoint(orderid):
    result = views.allocations(orderid, bus.uow)
    if not result:
        return 'Not found', 404
    return jsonify(result), 200
