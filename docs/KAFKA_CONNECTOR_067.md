

# PeaLang v0.67 Kafka Connector

v0.67 adds Apache Kafka integration to the v0.66 event-time streaming foundation.

## Capabilities
- Producer and consumer configuration through `KafkaConfig`.
- JSON event serialization/deserialization.
- Consumer groups, offset reset policy, manual commits, keys and headers.
- PLAINTEXT or secured client configuration, including SASL credentials.
- Batch publishing and bounded record consumption.
- `InMemoryKafkaBroker` for deterministic local tests without a Kafka service.

## Example
```python
from pealang.kafka_connector import KafkaConfig, KafkaConnector
cfg = KafkaConfig(["localhost:9092"], "employee-events", group_id="analytics")
kafka = KafkaConnector(cfg)
kafka.publish({"id":"e-1", "event_time":"2026-10-24T08:00:00Z"}, key="e-1")
for message in kafka.consume(max_records=100):
    print(message["value"])
kafka.commit()
```

The real backend is optional and requires `kafka-python`; the PeaLang core remains dependency-light.


