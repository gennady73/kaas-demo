#!/usr/bin/env python3
"""Run-scoped HTTPS continuity evidence sink. SQLite FULL/WAL commits precede acknowledgements."""
import contextlib,hashlib,hmac,http.server,json,os,re,sqlite3,ssl,threading,time,urllib.parse
from pathlib import Path

MAX_BODY=65536
DATA=Path(os.environ.get('CONTINUITY_DATA','/data'));DATA.mkdir(exist_ok=True)
DB=DATA/'events.sqlite'
TOKEN=Path(os.environ.get('CONTINUITY_TOKEN_FILE','/auth/token')).read_text().strip()
LOCK=threading.RLock()
@contextlib.contextmanager
def database():
    c=sqlite3.connect(str(DB),timeout=10);c.execute('PRAGMA busy_timeout=10000');c.execute('PRAGMA synchronous=FULL')
    try:yield c
    finally:c.close()
with database() as c:
    c.execute('PRAGMA journal_mode=WAL')
    c.executescript('''CREATE TABLE IF NOT EXISTS runs(run TEXT PRIMARY KEY,hash TEXT NOT NULL,plan TEXT NOT NULL,registered REAL NOT NULL,stopped TEXT);
     CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,run TEXT NOT NULL,hash TEXT NOT NULL,client TEXT NOT NULL,n INTEGER NOT NULL,kind TEXT NOT NULL,at REAL NOT NULL,body TEXT NOT NULL,digest TEXT NOT NULL,UNIQUE(run,client,n));
     CREATE INDEX IF NOT EXISTS events_run_kind ON events(run,kind);
     CREATE INDEX IF NOT EXISTS events_run_client ON events(run,client);''')

def compact(x):return json.dumps(x,separators=(',',':'),ensure_ascii=False).encode()
def disk():
    s=os.statvfs(DATA);total=s.f_blocks*s.f_frsize;free=s.f_bavail*s.f_frsize
    return {'total_bytes':total,'available_bytes':free,'used_fraction':1-free/total if total else 1,'database_bytes':DB.stat().st_size,'wal_bytes':Path(str(DB)+'-wal').stat().st_size if Path(str(DB)+'-wal').exists() else 0}
def summary(run):
    with database() as c:
        row=c.execute('SELECT hash,plan,stopped FROM runs WHERE run=?',(run,)).fetchone()
        if not row:return None
        counts=dict(c.execute('SELECT kind,count(*) FROM events WHERE run=? GROUP BY kind',(run,)))
        clients={}
        for client,n,last in c.execute('SELECT client,count(*),max(at) FROM events WHERE run=? GROUP BY client',(run,)):
            types=dict(c.execute('SELECT kind,count(*) FROM events WHERE run=? AND client=? GROUP BY kind',(run,client)))
            terminal=c.execute("SELECT body FROM events WHERE run=? AND client=? AND kind='client_end' ORDER BY n DESC LIMIT 1",(run,client)).fetchone()
            clients[client]={'event_count':n,'last_at_ms':last,'counts':types,'terminal':json.loads(terminal[0]) if terminal else None}
        return {'run_id':run,'plan_sha256':row[0],'stopped':row[2],'event_count':sum(counts.values()),'counts':counts,'clients':clients,'disk':disk()}

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def setup(self):
        super().setup();self.connection.settimeout(180)
    def log_message(self,*args):pass
    def reply(self,status,obj):
        b=compact(obj);self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def authorized(self):return hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+TOKEN)
    def do_GET(self):
        path=urllib.parse.urlsplit(self.path);parts=path.path.strip('/').split('/')
        try:
            if path.path=='/healthz':
                with database() as c:c.execute('SELECT 1').fetchone()
                return self.reply(200,{'healthy':True,'disk':disk(),'synchronous':'FULL','journal':'WAL'})
            if not self.authorized():return self.reply(401,{'error':'unauthorized'})
            if len(parts)!=3 or parts[0]!='runs':return self.reply(404,{'error':'unknown endpoint'})
            run,action=parts[1:];s=summary(run)
            if s is None:return self.reply(404,{'error':'unknown run'})
            if action=='readiness':
                if urllib.parse.parse_qs(path.query).get('plan_sha256')!=[s['plan_sha256']]:return self.reply(409,{'error':'plan hash mismatch'})
                return self.reply(200,{'run_id':run,'plan_sha256':s['plan_sha256'],'durable':True,'ready_clients':[k for k,v in s['clients'].items() if v['counts'].get('client_ready')==1],'stopped':s['stopped']})
            if action=='summary':return self.reply(200,s)
            if action=='export':
                # Stable transaction snapshot, exported after all clients finish for final reconciliation.
                with database() as c:
                    c.execute('BEGIN')
                    rows=c.execute('SELECT body,digest FROM events WHERE run=? ORDER BY client,n',(run,))
                    self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.send_header('Connection','close');self.end_headers()
                    for body,digest in rows:self.wfile.write(compact({'event_json':body,'event_sha256':digest})+b'\n')
                self.close_connection=True;return
            if action=='seal':
                with database() as c:
                    p=json.loads(c.execute('SELECT plan FROM runs WHERE run=?',(run,)).fetchone()[0]);clients=p['clients']
                    complete=not s['stopped'] and set(s['clients'])==set(clients) and all(s['clients'][x]['terminal'] and s['clients'][x]['terminal'].get('complete') is True for x in clients)
                    return self.reply(200,{'run_id':run,'plan_sha256':s['plan_sha256'],'complete':bool(complete),'event_count':s['event_count'],'client_event_counts':{x:v['event_count'] for x,v in s['clients'].items()},'sqlite_synchronous':'FULL','sealed_at_ms':int(time.time()*1000)})
            return self.reply(404,{'error':'unknown endpoint'})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:return self.reply(500,{'error':'collector read failure'})
    def do_POST(self):
        if not self.authorized():return self.reply(401,{'error':'unauthorized'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=MAX_BODY:return self.reply(413,{'error':'bounded JSON body required'})
            obj=json.loads(self.rfile.read(size));path=urllib.parse.urlsplit(self.path).path
            if path=='/register':
                raw=obj['plan_json'];p=json.loads(raw);digest=hashlib.sha256(raw.encode()).hexdigest();run=p['run_id']
                if digest!=obj['plan_sha256'] or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',run) or p.get('mode')!='sandbox_continuity' or not p.get('execution_ready') or not p.get('execution_enabled') or p.get('stage') not in ['15m','60m','24h'] or len(p.get('clients',[]))!=8:return self.reply(400,{'error':'reviewed armed continuity plan required'})
                with LOCK,database() as c:
                    prior=c.execute('SELECT hash FROM runs WHERE run=?',(run,)).fetchone()
                    if prior and prior[0]!=digest:return self.reply(409,{'error':'run already registered with different plan'})
                    c.execute('INSERT OR IGNORE INTO runs VALUES(?,?,?,?,NULL)',(run,digest,raw,time.time()));c.commit()
                return self.reply(201,{'run_id':run,'plan_sha256':digest,'durable':True})
            match=re.fullmatch(r'/runs/([A-Za-z0-9_-]{1,64})/stop',path)
            if match:
                with LOCK,database() as c:c.execute('UPDATE runs SET stopped=? WHERE run=?',('operator_stop',match.group(1)));c.commit()
                return self.reply(200,{'stopped':True})
            if path!='/events':return self.reply(404,{'error':'unknown endpoint'})
            raw=obj['event_json'];digest=hashlib.sha256(raw.encode()).hexdigest();e=json.loads(raw)
            if digest!=obj['event_sha256']:return self.reply(400,{'error':'event hash mismatch'})
            with LOCK,database() as c:
                row=c.execute('SELECT hash,plan,stopped FROM runs WHERE run=?',(e['run_id'],)).fetchone()
                if not row or row[0]!=e['plan_sha256']:return self.reply(409,{'error':'unregistered run/plan'})
                plan=json.loads(row[1]);client=e['client_id'];prefix=e['run_id']+'/'+client+'/'
                if client not in plan['clients'] or not e['event_id'].startswith(prefix) or not e['event_id'][len(prefix):].isdigit():return self.reply(400,{'error':'invalid event identity'})
                n=int(e['event_id'][len(prefix):]);prior=c.execute('SELECT body,digest FROM events WHERE id=?',(e['event_id'],)).fetchone()
                if prior:
                    if prior!=(raw,digest):return self.reply(409,{'error':'conflicting event body'})
                    return self.reply(200,{'event_id':e['event_id'],'event_sha256':digest,'durable':True})
                if row[2] and e['type']=='attempt':return self.reply(409,{'error':'run stopped'})
                if disk()['used_fraction']>0.8:
                    c.execute('UPDATE runs SET stopped=? WHERE run=?',('evidence_storage_threshold',e['run_id']));c.commit();return self.reply(507,{'error':'evidence storage threshold'})
                if e['type']=='client_error':c.execute('UPDATE runs SET stopped=? WHERE run=?',('client_error',e['run_id']))
                c.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?)',(e['event_id'],e['run_id'],e['plan_sha256'],client,n,e['type'],e['at_ms'],raw,digest));c.commit()
            return self.reply(201,{'event_id':e['event_id'],'event_sha256':digest,'durable':True})
        except (KeyError,ValueError,TypeError,json.JSONDecodeError):return self.reply(400,{'error':'invalid event/plan JSON'})
        except sqlite3.IntegrityError:return self.reply(409,{'error':'conflicting event sequence'})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:return self.reply(500,{'error':'collector persistence failure'})

if __name__=='__main__':
    os.umask(0o077)
    server=http.server.ThreadingHTTPServer(('0.0.0.0',8443),Handler);server.daemon_threads=True
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain('/tls/tls.crt','/tls/tls.key');server.socket=ctx.wrap_socket(server.socket,server_side=True)
    print('Continuity collector HTTPS ready; SQLite FULL/WAL; no credentials logged',flush=True)
    server.serve_forever(poll_interval=0.5)
