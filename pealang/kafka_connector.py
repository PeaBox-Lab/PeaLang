
"""PeaLang v0.67 Kafka connector with optional kafka-python backend."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator
import json, time

class KafkaConnectorError(RuntimeError): pass

@dataclass
class KafkaConfig:
    bootstrap_servers: list[str] | str
    topic: str
    group_id: str | None = None
    client_id: str = "pealang"
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = False
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def client_options(self):
        opts={"bootstrap_servers":self.bootstrap_servers,"client_id":self.client_id,
              "security_protocol":self.security_protocol}
        if self.sasl_mechanism: opts["sasl_mechanism"]=self.sasl_mechanism
        if self.sasl_username is not None: opts["sasl_plain_username"]=self.sasl_username
        if self.sasl_password is not None: opts["sasl_plain_password"]=self.sasl_password
        opts.update(self.extra); return opts

class KafkaConnector:
    def __init__(self, config: KafkaConfig, producer=None, consumer=None):
        self.config=config; self._producer=producer; self._consumer=consumer

    def _producer_client(self):
        if self._producer is not None: return self._producer
        try: from kafka import KafkaProducer
        except ImportError as exc: raise KafkaConnectorError("Kafka support requires kafka-python") from exc
        self._producer=KafkaProducer(value_serializer=lambda v: json.dumps(v,default=str).encode("utf-8"),**self.config.client_options())
        return self._producer

    def _consumer_client(self):
        if self._consumer is not None: return self._consumer
        try: from kafka import KafkaConsumer
        except ImportError as exc: raise KafkaConnectorError("Kafka support requires kafka-python") from exc
        opts=self.config.client_options(); opts.update({"group_id":self.config.group_id,"auto_offset_reset":self.config.auto_offset_reset,
            "enable_auto_commit":self.config.enable_auto_commit,"value_deserializer":lambda v: json.loads(v.decode("utf-8"))})
        self._consumer=KafkaConsumer(self.config.topic,**opts); return self._consumer

    def publish(self, event: dict, key: str | bytes | None=None, headers=None):
        k=key.encode("utf-8") if isinstance(key,str) else key
        return self._producer_client().send(self.config.topic,value=event,key=k,headers=headers).get(timeout=30)

    def publish_many(self, events: Iterable[dict]):
        results=[self.publish(e) for e in events]; self.flush(); return results

    def consume(self, max_records: int | None=None) -> Iterator[dict]:
        count=0
        for msg in self._consumer_client():
            yield {"value":msg.value,"key":msg.key,"topic":msg.topic,"partition":msg.partition,"offset":msg.offset,"timestamp":msg.timestamp}
            count+=1
            if max_records is not None and count>=max_records: break

    def commit(self):
        c=self._consumer_client()
        if hasattr(c,"commit"): c.commit()

    def flush(self):
        p=self._producer_client()
        if hasattr(p,"flush"): p.flush()

    def close(self):
        for obj in (self._producer,self._consumer):
            if obj is not None and hasattr(obj,"close"): obj.close()

class InMemoryKafkaBroker:
    """Deterministic development/test broker with Kafka-like topic offsets."""
    def __init__(self): self.topics={}
    def publish(self,topic,value,key=None):
        q=self.topics.setdefault(topic,[]); offset=len(q); q.append({"value":value,"key":key,"topic":topic,"partition":0,"offset":offset,"timestamp":int(time.time()*1000)}); return offset
    def consume(self,topic,offset=0,max_records=None):
        rows=self.topics.get(topic,[])[offset:]
        return rows if max_records is None else rows[:max_records]

