from  kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def send_move_request(data: dict):
    producer.send("truck.move.requested", data)
    producer.flush()