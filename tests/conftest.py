import time
from pathlib import Path

import pytest
import requests
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlalchemy.sql import text
from tenacity import retry, stop_after_delay

import config
from adapters.orm import start_mappers, mapper_registry

@pytest.fixture
def in_memory_db():
    engine = create_engine('sqlite:///:memory:')
    mapper_registry.metadata.create_all(engine)
    return engine

@pytest.fixture
def session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()

@pytest.fixture
def session(session_factory):
    return session_factory()

@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(engine):
    return engine.connect()

@pytest.fixture(scope='session')
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    mapper_registry.metadata.create_all(engine)
    return engine

@pytest.fixture
def postgres_session_factory(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)
    clear_mappers()

@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()

@pytest.fixture
def add_stock(postgres_session):
    batches_added = set()
    skus_added = set()

    def _add_stock(lines):
        for ref, sku, qty, eta in lines:
            postgres_session.execute(
                text('''
                    INSERT INTO batches (reference, sku, _purchased_quantity, eta)
                    VALUES (:ref, :sku, :qty, :eta)
                '''),
                {'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta},
            )
            [[batch_id]] = postgres_session.execute(
                text('SELECT id FROM batches WHERE reference=:ref AND sku=:sku'),
                {'ref': ref, 'sku': sku},
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        postgres_session.execute(
            text('DELETE FROM allocations WHERE batch_id=:batch_id'),
            {'batch_id': batch_id},
        )
        postgres_session.execute(
            text('DELETE FROM batches WHERE id=:batch_id'),
            {'batch_id': batch_id},
        )

    for sku in skus_added:
        postgres_session.execute(
            text('DELETE FROM order_lines WHERE sku=:sku'),
            {'sku': sku},
        )

    postgres_session.commit()

@retry(stop=stop_after_delay(10))
def wait_for_web_app_to_come_up():
    url = config.get_api_url()
    return requests.get(url)

@pytest.fixture
def restart_api():
    (Path(__file__).parent / '../entrypoints/flask_app.py').touch()
    time.sleep(0.5)
    wait_for_web_app_to_come_up()

@retry(stop=stop_after_delay(10))
def wait_for_redis_to_come_up():
    r = redis.Redis(**config.get_redis_host_and_port())
    return r.ping()

@pytest.fixture
def restart_redis_pubsub():
    wait_for_redis_to_come_up()
