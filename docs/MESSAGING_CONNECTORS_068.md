

# PeaLang v0.68 Messaging Connectors

v0.68 completes the first scalable-data phase with RabbitMQ and WebSocket connectivity alongside the v0.67 Kafka connector.

## RabbitMQ
- JSON publishing and consumption.
- Queue declaration, durability, routing keys and exchanges.
- QoS/prefetch configuration.
- Explicit acknowledgements and negative acknowledgements with requeue control.
- Optional `pika` backend.

## WebSocket
- Client connections with headers and timeouts.
- JSON send/receive with text fallback.
- Bounded or continuous receive streams.
- Optional `websocket-client` backend.

## Local development
`InMemoryMessageBus` provides dependency-free deterministic messaging for unit tests and local workflows.


