"""Dedicated HTTPS evidence endpoint. Does not deploy or create credentials."""
import argparse
import hmac
import json
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from store import Store, Rejected, encode, parse

class TLSServer(HTTPServer):
    # Bound TLS handshake as well as request processing; no HTTP fallback.
    def __init__(self,address,handler_type,context):
        self.context=context
        super().__init__(address,handler_type)
    def get_request(self):
        sock,address=super().get_request();sock.settimeout(2)
        try:return self.context.wrap_socket(sock,server_side=True),address
        except BaseException:
            sock.close()
            raise
    def handle_error(self,request,address): pass

def handler(store, writer_token, owner_token):
    class Handler(BaseHTTPRequestHandler):
        # No access logging, request bodies, errors or bearer values on stdout/stderr.
        def log_message(self,*args): pass
        def respond(self,status,body,content_type='application/json'):
            if not isinstance(body,bytes): body=encode(body)
            self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self): self.dispatch('GET')
        def do_POST(self): self.dispatch('POST')
        def dispatch(self,method):
            self.connection.settimeout(2)
            allowed={('POST','/v1/events'):'writer',('POST','/v1/stop'):'owner',('POST','/v1/seal'):'owner',('GET','/v1/export'):'owner'}
            role=allowed.get((method,self.path))
            if role is None:return self.respond(404,{'error':'endpoint'})
            expected=writer_token if role=='writer' else owner_token
            try:authenticated=hmac.compare_digest(self.headers.get('Authorization','').encode('ascii'), ('Bearer '+expected).encode('ascii'))
            except (UnicodeError,AttributeError):authenticated=False
            if not authenticated:return self.respond(401,{'error':'authentication'})
            try:
                if method=='POST':
                    if self.headers.get('Transfer-Encoding') is not None:raise Rejected('body')
                    size=int(self.headers.get('Content-Length','-1'))
                    if size<0 or size>20000:raise Rejected('body')
                    raw=self.rfile.read(size)
                    if len(raw)!=size:raise Rejected('body')
                    body=parse(raw)
                if self.path=='/v1/events':
                    status,ack=store.event(body);return self.respond(status,ack)
                if self.path=='/v1/stop':
                    if body!={}:raise Rejected('body')
                    return self.respond(200,store.stop())
                if self.path=='/v1/seal':
                    if body!={}:raise Rejected('body')
                    return self.respond(200,store.seal())
                return self.respond(200,store.export(),'application/x-ndjson')
            except Rejected:return self.respond(409,{'error':'rejected'})
            except Exception:return self.respond(503,{'error':'unavailable'})
    return Handler

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args()
    cfg=json.loads(Path(args.config).read_text())
    # Absolute mounted paths, no token CLI/env values and no HTTP mode.
    writer=Path(cfg['writer_token_file']).read_text().strip();owner=Path(cfg['owner_token_file']).read_text().strip()
    if len(writer)<32 or len(owner)<32 or writer==owner:raise SystemExit('invalid authentication files')
    store=Store(cfg['database'],cfg['run_id'],cfg['plan_sha256'])
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cfg['tls_cert_file'],cfg['tls_key_file'])
    server=TLSServer(('0.0.0.0',8443),handler(store,writer,owner),context)
    try:server.serve_forever()
    finally:server.server_close();store.close()

if __name__=='__main__':main()
