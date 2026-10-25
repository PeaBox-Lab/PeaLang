


"""PeaLang v0.68 RabbitMQ and WebSocket connectors with optional backends."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator
import json, queue

class MessagingConnectorError(RuntimeError): pass

@dataclass
class RabbitMQConfig:
    host: str="localhost"
    port: int=5672
    virtual_host: str="/"
    username: str="guest"
    password: str="guest"
    queue: str="pealang"
    exchange: str=""
    routing_key: str|None=None
    durable: bool=True
    prefetch_count: int=100
    heartbeat: int=60
    extra: dict[str,Any]=field(default_factory=dict)

class RabbitMQConnector:
    def __init__(self,config:RabbitMQConfig,connection=None): self.config=config; self._connection=connection; self._channel=None
    def _connect(self):
        if self._connection is None:
            try: import pika
            except ImportError as exc: raise MessagingConnectorError("RabbitMQ support requires pika") from exc
            credentials=pika.PlainCredentials(self.config.username,self.config.password)
            params=pika.ConnectionParameters(self.config.host,self.config.port,self.config.virtual_host,credentials,heartbeat=self.config.heartbeat,**self.config.extra)
            self._connection=pika.BlockingConnection(params)
        if self._channel is None:
            self._channel=self._connection.channel(); self._channel.queue_declare(queue=self.config.queue,durable=self.config.durable); self._channel.basic_qos(prefetch_count=self.config.prefetch_count)
        return self._channel
    def publish(self,event:dict,routing_key=None):
        ch=self._connect(); body=json.dumps(event,default=str).encode("utf-8"); key=routing_key or self.config.routing_key or self.config.queue
        try:
            import pika; props=pika.BasicProperties(content_type="application/json",delivery_mode=2 if self.config.durable else 1)
        except ImportError: props=None
        ch.basic_publish(exchange=self.config.exchange,routing_key=key,body=body,properties=props); return True
    def publish_many(self,events:Iterable[dict]): return sum(1 for e in events if self.publish(e))
    def consume(self,max_messages:int|None=None,auto_ack:bool=False)->Iterator[dict]:
        ch=self._connect(); count=0
        for method,props,body in ch.consume(self.config.queue,auto_ack=auto_ack,inactivity_timeout=1):
            if method is None: continue
            yield {"value":json.loads(body.decode("utf-8")),"delivery_tag":method.delivery_tag,"routing_key":method.routing_key,"properties":props}
            count+=1
            if max_messages is not None and count>=max_messages: break
        if hasattr(ch,"cancel"): ch.cancel()
    def ack(self,delivery_tag): self._connect().basic_ack(delivery_tag=delivery_tag)
    def nack(self,delivery_tag,requeue=True): self._connect().basic_nack(delivery_tag=delivery_tag,requeue=requeue)
    def close(self):
        if self._connection is not None and hasattr(self._connection,"close"): self._connection.close()

@dataclass
class WebSocketConfig:
    url:str
    headers:dict[str,str]=field(default_factory=dict)
    timeout:float=30.0

class WebSocketConnector:
    def __init__(self,config:WebSocketConfig,client=None): self.config=config; self._client=client
    def _connect(self):
        if self._client is None:
            try: import websocket
            except ImportError as exc: raise MessagingConnectorError("WebSocket support requires websocket-client") from exc
            header=[f"{k}: {v}" for k,v in self.config.headers.items()]
            self._client=websocket.create_connection(self.config.url,header=header,timeout=self.config.timeout)
        return self._client
    def send(self,event): self._connect().send(json.dumps(event,default=str)); return True
    def receive(self):
        value=self._connect().recv()
        if isinstance(value,bytes): value=value.decode("utf-8")
        try: return json.loads(value)
        except (json.JSONDecodeError,TypeError): return value
    def stream(self,max_messages=None):
        n=0
        while max_messages is None or n<max_messages:
            yield self.receive(); n+=1
    def close(self):
        if self._client is not None and hasattr(self._client,"close"): self._client.close()

class InMemoryMessageBus:
    """Local deterministic queue/topic bus for connector tests and development."""
    def __init__(self): self.queues={}
    def publish(self,name,event): self.queues.setdefault(name,queue.Queue()).put(event); return True
    def consume(self,name,max_messages=None):
        q=self.queues.setdefault(name,queue.Queue()); rows=[]
        while not q.empty() and (max_messages is None or len(rows)<max_messages): rows.append(q.get_nowait())
        return rows



