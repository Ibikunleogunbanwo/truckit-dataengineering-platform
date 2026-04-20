from kafka.errors import KafkaError
from app.core.kafka import get_producer, TOPIC


def send_move_request(data: dict):
    producer = get_producer()
    try:
        future = producer.send(TOPIC, data)
        record_metadata = future.get(timeout=10)
        print(f"Message sent → topic: {record_metadata.topic}, partition: {record_metadata.partition}, offset: {record_metadata.offset}")
    except KafkaError as e:
        print(f"Failed to send message: {e}")
        raise
