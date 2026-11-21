"""EVQ simulated charging API. DO NOT expose to public internet."""
import os, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from evq.service import Service
svc = Service(os.environ.get('EVQ_DB','evq.sqlite3'))
class API(BaseHTTPRequestHandler):
    def send(self, code, body):
        b=json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        p=urlsplit(self.path).path
        if p=='/api/stations': self.send(200,svc.stations())
        elif p=='/api/sessions': self.send(200,svc.history())
        elif p=='/api/health': self.send(200,{'ok':True,'mode':'simulation'})
        else: self.send(404,{'error':'Not found'})
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>4096: raise ValueError('Request too large')
            data=json.loads(self.rfile.read(n) or '{}')
            p=urlsplit(self.path).path.split('/')
            if p==['','api','sessions']:
                out=svc.start(data.get('station'),data.get('kwh'),data.get('tariff','standard'))
                self.send(201,out)
            elif len(p)==5 and p[:3]==['','api','sessions']:
                out=svc.change(p[3],p[4],data.get('kwh'))
                self.send(200,out)
            else: self.send(404,{'error':'Not found'})
        except (ValueError,TypeError,AttributeError) as e: self.send(400,{'error':str(e)})
        except KeyError as e: self.send(404,{'error':str(e)})
if __name__=='__main__':
    host=os.environ.get('EVQ_HOST','127.0.0.1'); port=int(os.environ.get('EVQ_PORT','8000'))
    print(f'EVQ API http://{host}:{port}')
    ThreadingHTTPServer((host,port),API).serve_forever()
