from kafka import KafkaProducer
import json

from app.core.settings import get_env

TOPIC = get_env("KAFKA_TOPIC")
BOOTSTRAP_SERVERS = get_env("KAFKA_BOOTSTRAP_SERVERS")

_producer = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    return _producer
