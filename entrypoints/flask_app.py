import datetime as dt

from flask import Flask, request, jsonify

import views
from adapters import orm
from service_layer import handlers, unit_of_work, messagebus
from domain import commands

orm.start_mappers()
app = Flask(__name__)

@app.route('/add_batch', methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = dt.datetime.fromisoformat(eta).date()

    uow = unit_of_work.SqlAlchemyUnitOfWork()
    event = commands.CreateBatch(request.json['ref'], request.json['sku'], request.json['qty'], eta)
    messagebus.handle(event, uow)
    return 'OK', 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        event = commands.Allocate(request.json['orderid'], request.json['sku'], request.json['qty'])
        messagebus.handle(event, uow)
        return 'OK', 202
    except handlers.InvalidSku as exc:
        return {'message': str(exc)}, 400

@app.route('/allocations/<orderid>', methods=['GET'])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid, uow)
    if not result:
        return 'Not found', 404
    return jsonify(result), 200
