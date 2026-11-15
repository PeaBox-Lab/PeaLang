"""Streaming and real-time primitives for PeaLang (v2.5.0).

Provides:
- Kafka/Pulsar connection primitives
- Stream processing operators
- Schema registry stub
- Windowed aggregations
- Checkpointing support
"""

from __future__ import annotations

import json
import hashlib
import time
import threading
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Kafka/Pulsar Connection Primitives
# ---------------------------------------------------------------------------

class KafkaConfig:
    """Configuration for Kafka connection."""
    def __init__(
        self,
        bootstrap_servers: List[str] = None,
        group_id: str = "pealang-consumer",
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
    ):
        self.bootstrap_servers = bootstrap_servers or ["localhost:9092"]
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit


class KafkaProducer:
    """Stub Kafka producer for PeaLang.

    In production would connect to a real Kafka cluster.
    """

    def __init__(self, config: KafkaConfig = None):
        self.config = config or KafkaConfig()
        self._connected = False
        self._topic: str | None = None

    def connect(self) -> bool:
        """Simulate connection to Kafka cluster."""
        # In production: self._connected = True via confluent-kafka or kafka-python
        self._connected = True
        self._topic = None
        return self._connected

    def publish(self, topic: str, message: Union[str, Dict[str, Any]], key: str | None = None) -> bool:
        """Publish a message to *topic*.

        Returns True if the publish was accepted (stub).
        """
        if not self._connected:
            raise RuntimeError("Kafka producer not connected")
        self._topic = topic
        # Normalize message to JSON bytes
        if isinstance(message, str):
            payload = message.encode("utf-8")
        elif isinstance(message, dict):
            payload = json.dumps(message).encode("utf-8")
        else:
            payload = str(message).encode("utf-8")
        # Stub: just record what would be published
        return True

    def close(self) -> None:
        """Close the producer connection."""
        self._connected = False


class KafkaConsumer:
    """Stub Kafka consumer for PeaLang.

    In production would consume from a real Kafka cluster.
    """

    def __init__(self, config: KafkaConfig = None):
        self.config = config or KafkaConfig()
        self._connected = False
        self._assigned_partitions: List[tuple] = []
        self._offsets: Dict[tuple, int] = {}

    def subscribe(self, topics: List[str]) -> None:
        """Subscribe to *topics*."""
        # Stub: just remember the topics
        pass

    def assign(self, partitions: List[tuple]) -> None:
        """Assign *partitions* to consume."""
        self._assigned_partitions = partitions

    def connect(self) -> bool:
        """Simulate connection to Kafka cluster."""
        self._connected = True
        return self._connected

    def poll(self, timeout_ms: int = 1000) -> Optional[Dict[str, Any]]:
        """Poll for a message.

        Returns a dict with keys: topic, partition, offset, key, value,
        or None if no message is available (stub always returns None).
        """
        if not self._connected:
            raise RuntimeError("Kafka consumer not connected")
        # Stub: no real polling — return None
        return None

    def commit(self) -> bool:
        """Commit offsets."""
        # Stub
        return True

    def close(self) -> None:
        """Close the consumer connection."""
        self._connected = False


# ---------------------------------------------------------------------------
# Stream Processing Operators
# ---------------------------------------------------------------------------

class WindowResult:
    """Result of a windowed aggregation."""

    def __init__(self, window_id: str, values: List[Any], count: int, timestamp: float):
        self.window_id = window_id
        self.values = values
        self.count = count
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_id": self.window_id,
            "count": self.count,
            "timestamp": self.timestamp,
            "values": self.values,
        }


class KTable:
    """Key-value store for stream processing — changelog-backed."""

    def __init__(self, name: str):
        self.name = name
        self._store: Dict[str, Any] = {}
        self._changelog: List[Dict[str, Any]] = []

    def put(self, key: str, value: Any) -> None:
        old = self._store.get(key)
        self._store[key] = value
        self._changelog.append({"op": "PUT", "key": key, "value": value, "previous": old})

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        old = self._store.pop(key, None)
        self._changelog.append({"op": "DELETE", "key": key, "value": old})

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "store": dict(self._store), "changelog": self._changelog}


# ---------------------------------------------------------------------------
# Schema Registry Stub
# ---------------------------------------------------------------------------

class SchemaRegistry:
    """Minimal schema registry for stream topics."""

    def __init__(self, storage_path: str = ".peaschema"):
        self.storage_path = storage_path
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._evolution: Dict[str, List[Dict[str, Any]]] = {}
        Path(storage_path).mkdir(parents=True, exist_ok=True)

    def register(self, topic: str, schema: Dict[str, Any], schema_id: int | None = None) -> int:
        """Register a schema for *topic*.

        Returns the assigned schema ID.
        """
        sid = schema_id or len(self._schemas.get(topic, [])) + 1
        self._schemas.setdefault(topic, {})[str(sid)] = {
            "schema": schema,
            "id": sid,
            "registered_at": time.time(),
        }
        return sid

    def get(self, topic: str, schema_id: int | None = None) -> Dict[str, Any]:
        """Get schema for *topic*.

        Returns dict with schema details or raises KeyError.
        """
        schemas = self._schemas.get(topic, {})
        if schema_id is not None:
            return schemas.get(str(schema_id), {"error": "schema not found"})
        # Return the latest
        if schemas:
            latest_id = max(int(k) for k in schemas.keys())
            return schemas[str(latest_id)]
        raise KeyError(f"No schema registered for topic: {topic}")


# ---------------------------------------------------------------------------
# Windowed Aggregations
# ---------------------------------------------------------------------------

def tumbling_window(
    stream: List[Dict[str, Any]],
    window_size_sec: int,
    timestamp_key: str = "timestamp",
) -> List[WindowResult]:
    """Partition a stream into tumbling (non-overlapping) windows.

    *stream* is a list of records each expected to have a numeric
    *timestamp_key* field (seconds since epoch).

    Returns a list of WindowResult — one per window.
    """
    if not stream:
        return []

    # Sort by timestamp
    sorted_stream = sorted(stream, key=lambda r: r.get(timestamp_key, 0))

    windows: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for record in sorted_stream:
        ts = record.get(timestamp_key, 0)
        window_id = int(ts // window_size_sec)
        windows[window_id].append(record)

    results: List[WindowResult] = []
    for window_id, records in sorted(windows.items()):
        window_start = window_id * window_size_sec
        window_end = window_start + window_size_sec
        results.append(WindowResult(
            window_id=f"w-{window_id}",
            values=records,
            count=len(records),
            timestamp=time.time(),
        ))
    return results


def sliding_window(
    stream: List[Dict[str, Any]],
    window_size_sec: int,
    slide_sec: int,
    timestamp_key: str = "timestamp",
) -> List[WindowResult]:
    """Partition a stream into sliding windows (overlapping).

    *slide_sec* controls how far the window advances each step.
    """
    if not stream:
        return []

    sorted_stream = sorted(stream, key=lambda r: r.get(timestamp_key, 0))

    results: List[WindowResult] = []
    # Start windows at multiples of slide_sec relative to the first timestamp
    first_ts = sorted_stream[0].get(timestamp_key, 0)
    start_window = int(first_ts // slide_sec) * slide_sec

    # Generate windows that overlap the data range
    window_id = start_window
    current_vals: List[Dict[str, Any]] = []

    for record in sorted_stream:
        ts = record.get(timestamp_key, 0)
        # Advance window_id until we're past the record
        while int(ts // window_id) > window_id if window_id else False:
            # This is a simplistic approach; a real implementation would
            # maintain a sliding buffer.
            window_id += 1

        # Add to current window buffer
        # We'll collect records whose timestamps fall in the current window
        window_start = window_id * slide_sec
        window_end = window_start + window_size_sec

        if window_start <= ts < window_end:
            current_vals.append(record)
        else:
            # Emit previous window if it has records
            if current_vals:
                results.append(WindowResult(
                    window_id=f"w-{window_id - 1}",
                    values=current_vals,
                    count=len(current_vals),
                    timestamp=time.time(),
                ))
                current_vals = [record]
                window_id += 1

    # Flush remaining
    if current_vals:
        results.append(WindowResult(
            window_id=f"w-{window_id}",
            values=current_vals,
            count=len(current_vals),
            timestamp=time.time(),
        ))

    return results


# ---------------------------------------------------------------------------
# Checkpointing Support
# ---------------------------------------------------------------------------

class Checkpoint:
    """A checkpoint for stream processing exactly-once state."""

    def __init__(self, id: str, timestamp: float, state: Dict[str, Any]):
        self.id = id
        self.timestamp = timestamp
        self.state = state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "state": self.state,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Checkpoint":
        return Checkpoint(id=d["id"], timestamp=d["timestamp"], state=d.get("state", {}))


class CheckpointManager:
    """Manage checkpoints for a stream processing job."""

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self._checkpoints: Dict[str, Checkpoint] = {}
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: Checkpoint) -> None:
        """Persist a checkpoint to disk."""
        path = Path(self.checkpoint_dir) / f"{checkpoint.id}.json"
        path.write_text(json.dumps(checkpoint.to_dict(), indent=2))
        self._checkpoints[checkpoint.id] = checkpoint

    def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load a checkpoint by ID."""
        # Try disk first
        path = Path(self.checkpoint_dir) / f"{checkpoint_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            cp = Checkpoint.from_dict(data)
            self._checkpoints[checkpoint_id] = cp
            return cp
        # Try in-memory
        if checkpoint_id in self._checkpoints:
            return self._checkpoints[checkpoint_id]
        return None


# ---------------------------------------------------------------------------
# Namespace exporter
# ---------------------------------------------------------------------------

def build_streaming_namespace() -> Dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "KafkaConfig": KafkaConfig,
        "KafkaProducer": KafkaProducer,
        "KafkaConsumer": KafkaConsumer,
        "KTable": KTable,
        "SchemaRegistry": SchemaRegistry,
        "WindowResult": WindowResult,
        "tumbling_window": tumbling_window,
        "sliding_window": sliding_window,
        "Checkpoint": Checkpoint,
        "CheckpointManager": CheckpointManager,
        "build_streaming_namespace": build_streaming_namespace,
    }
