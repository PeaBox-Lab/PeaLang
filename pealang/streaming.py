"""PeaLang v0.66 event-time streaming primitives."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import json
from pathlib import Path


def _dt(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

@dataclass(frozen=True)
class Watermark:
    delay: timedelta
    def threshold(self,max_event_time): return max_event_time-self.delay

@dataclass(frozen=True)
class TumblingWindow:
    size: timedelta
    def bounds(self,event_time):
        ts=_dt(event_time); seconds=self.size.total_seconds()
        start=datetime.fromtimestamp((ts.timestamp()//seconds)*seconds,tz=timezone.utc)
        return start,start+self.size

@dataclass(frozen=True)
class SlidingWindow:
    size: timedelta
    slide: timedelta
    def bounds(self,event_time):
        ts=_dt(event_time); slide=self.slide.total_seconds(); size=self.size.total_seconds()
        anchor=(ts.timestamp()//slide)*slide; out=[]; cur=anchor
        while cur+size>ts.timestamp() and cur>=ts.timestamp()-size:
            out.append((datetime.fromtimestamp(cur,tz=timezone.utc),datetime.fromtimestamp(cur+size,tz=timezone.utc))); cur-=slide
        return out

class DeliveryLedger:
    """Persistent idempotency ledger supporting at-least-once processing with exactly-once sink effects."""
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.ids=set(self.path.read_text(encoding='utf-8').splitlines()) if self.path.exists() else set()
    def seen(self,event_id): return str(event_id) in self.ids
    def commit(self,event_id):
        eid=str(event_id)
        if eid not in self.ids:
            with self.path.open('a',encoding='utf-8') as fh: fh.write(eid+'\n')
            self.ids.add(eid)

class EventTimeStream:
    def __init__(self,time_field,id_field='id',watermark=None):
        self.time_field=time_field; self.id_field=id_field; self.watermark=watermark or Watermark(timedelta(0)); self.max_event_time=None; self.late=[]
    def accept(self,event):
        ts=_dt(event[self.time_field])
        if self.max_event_time is None or ts>self.max_event_time: self.max_event_time=ts
        if ts < self.watermark.threshold(self.max_event_time): self.late.append(event); return False
        return True
    def window(self,events,spec):
        buckets=defaultdict(list)
        for event in events:
            if not self.accept(event): continue
            bounds=spec.bounds(event[self.time_field]); bounds=[bounds] if isinstance(spec,TumblingWindow) else bounds
            for start,end in bounds: buckets[(start,end)].append(event)
        return dict(buckets)
    def deliver(self,events,sink,ledger=None):
        delivered=0
        for event in events:
            eid=event.get(self.id_field)
            if ledger and eid is not None and ledger.seen(eid): continue
            sink(event)
            if ledger and eid is not None: ledger.commit(eid)
            delivered+=1
        return delivered

