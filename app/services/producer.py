from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import os

TOPIC = os.getenv("KAFKA_TOPIC", "truck.move.requested")

_producer = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    return _producer


def send_move_request(data: dict):
    producer = get_producer()
    try:
        future = producer.send(TOPIC, data)
        record_metadata = future.get(timeout=10)
        print(f"Message sent → topic: {record_metadata.topic}, partition: {record_metadata.partition}, offset: {record_metadata.offset}")
    except KafkaError as e:
        print(f"Failed to send message: {e}")
        raise
