import datetime as dt

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from domain import model
from adapters import orm, repository
from services import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)

@app.route('/add_batch', methods=['POST'])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    eta = request.json['eta']
    if eta is not None:
        eta = dt.datetime.fromisoformat(eta).date()

    services.add_batch(
        request.json['ref'], request.json['sku'], request.json['qty'],
        eta, repo, session,
    )
    return 'OK', 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    try:
        batchref = services.allocate(
            request.json['orderid'], request.json['sku'], request.json['qty'],
            repo, session,
        )
        return jsonify({'batchref': batchref}), 201
    except (model.OutOfStock, services.InvalidSku) as exc:
        return jsonify({'message': str(exc)}), 400
