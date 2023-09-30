import datetime as dt

from flask import Flask, jsonify, request

from domain import model
from adapters import orm
from services import services, unit_of_work

orm.start_mappers()
app = Flask(__name__)

@app.route('/add_batch', methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = dt.datetime.fromisoformat(eta).date()

    uow = unit_of_work.SqlAlchemyUnitOfWork()
    services.add_batch(request.json['ref'], request.json['sku'], request.json['qty'], eta, uow)
    return 'OK', 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        batchref = services.allocate(request.json['orderid'], request.json['sku'], request.json['qty'], uow)
        return jsonify({'batchref': batchref}), 201
    except (model.OutOfStock, services.InvalidSku) as exc:
        return jsonify({'message': str(exc)}), 400
