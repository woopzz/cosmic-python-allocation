import time
from pathlib import Path

import pytest
import requests
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from tenacity import retry, stop_after_delay

import config
from adapters.orm import start_mappers, mapper_registry

@pytest.fixture
def in_memory_db():
    engine = create_engine('sqlite:///:memory:')
    mapper_registry.metadata.create_all(engine)
    return engine

@pytest.fixture
def sqlite_session_factory(in_memory_db):
    yield sessionmaker(bind=in_memory_db)

@pytest.fixture
def mappers():
    start_mappers()
    yield
    clear_mappers()

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
    yield sessionmaker(bind=postgres_db)

@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()

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
