"""Minimal HTTP runtime sidecar using Python stdlib."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from dataclasses import asdict,is_dataclass
from .runtime_service import RuntimeService
SERVICE=RuntimeService()
class Handler(BaseHTTPRequestHandler):
 def send_json(self,status,data):
  body=json.dumps(asdict(data) if is_dataclass(data) else data,default=str).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if self.path=='/health':return self.send_json(200,SERVICE.health())
  if self.path=='/ready':return self.send_json(200,SERVICE.readiness())
  return self.send_json(404,{'error':'not found'})
 def do_POST(self):
  try:data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
  except Exception:return self.send_json(400,{'error':'invalid json'})
  mapping={'/v1/compile':'compile','/v1/modules/load':'load','/v1/invoke':'invoke'}
  if self.path not in mapping:return self.send_json(404,{'error':'not found'})
  data['operation']=mapping[self.path];result=SERVICE.handle(data);return self.send_json(200 if result.get('ok',True) else 400,result)
 def log_message(self,*args):pass
def serve(host='127.0.0.1',port=8787):ThreadingHTTPServer((host,port),Handler).serve_forever()

