# PeaLang v0.66 Event-Time Streaming

v0.66 adds a compact streaming foundation on top of the v0.65 scalable execution layer.

## Capabilities
- Event-time processing using ISO timestamps or Python `datetime` values.
- Configurable watermarks and late-event capture.
- Tumbling windows and sliding windows.
- At-least-once processing with a persistent idempotency ledger for exactly-once sink effects.
- Restart-safe delivery ledger stored locally as an append-only file.

## Example
```python
from datetime import timedelta
from pealang.streaming import EventTimeStream, Watermark, TumblingWindow
stream = EventTimeStream("event_time", watermark=Watermark(timedelta(minutes=5)))
windows = stream.window(events, TumblingWindow(timedelta(minutes=10)))
```
