# PeaLang v0.79 Enterprise Integration Hardening

v0.79 standardizes reliability controls across PeaLang's existing connector ecosystem.

## Added
- Credential-provider abstraction with environment, mapping and chained providers.
- Shared connector error taxonomy for authentication, rate limits, timeouts and unavailability.
- Retry policy with exponential backoff, caps and jitter.
- Circuit-breaker state machine with closed, open and half-open recovery.
- Correlation IDs and execution-attempt evidence.
- Normalized TLS, proxy, timeout and correlation settings in `IntegrationProfile`.
- Connector health checks with latency and structured failure detail.

The module is additive: existing REST, GraphQL, cloud, enterprise, Kafka, RabbitMQ and WebSocket connectors remain compatible and may adopt these policies incrementally.
