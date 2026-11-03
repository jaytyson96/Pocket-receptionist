"""ONECALL local-only demo API. Never expose to a public interface.
Run: cd prototype && python server.py
No authentication: fictional information ONLY.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json, os, re, mimetypes
import pricing, database

HERE=Path(__file__).resolve().parent
DB_PATH=Path(os.environ.get('ONECALL_DEMO_DB', HERE / 'data' / 'onecall-demo.db'))
PUBLIC=HERE/'web'
MAX_BODY=16384

class Handler(BaseHTTPRequestHandler):
    database_path=DB_PATH
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()
    def respond(self,content,status=200):
        raw=json.dumps(content,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def fail(self,message,status=400):
        self.respond({'error':message},status)
    def read_body(self):
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            raise pricing.InputError('JSON content type required.')
        try:
            size=int(self.headers.get('Content-Length',''))
        except (TypeError,ValueError):
            raise pricing.InputError('Content-Length required.') from None
        if size<2 or size>MAX_BODY:
            raise pricing.InputError('Body too small or too large.')
        try:
            body=json.loads(self.rfile.read(size).decode('utf-8'))
        except (ValueError,UnicodeDecodeError):
            raise pricing.InputError('Invalid JSON.') from None
        if not isinstance(body,dict):
            raise pricing.InputError('JSON object expected.')
        return body
    def allowed_origin(self):
        origin=self.headers.get('Origin')
        if origin is None: return True
        host=self.headers.get('Host','')
        return origin==f'http://{host}' and host in ('127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port))
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/health':
            return self.respond({'ok':True,'mode':'fictional-local-only','ai':False,'real_customers':False})
        if path=='/api/rates':
            return self.respond({'rates':database.rates(self.database_path)})
        if path=='/api/enquiries':
            return self.respond({'enquiries':database.list_all(self.database_path)})
        found=re.fullmatch(r'/api/enquiries/(\d+)',path)
        if found:
            item=database.get(self.database_path,int(found.group(1)))
            return self.respond({'enquiry':item}) if item else self.fail('Not found',404)
        if path=='/': path='/index.html'
        file=(PUBLIC/path.lstrip('/')).resolve()
        if not file.is_relative_to(PUBLIC.resolve()) or not file.is_file():
            return self.fail('Not found',404)
        raw=file.read_bytes()
        mime=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_POST(self):
        if not self.allowed_origin(): return self.fail('Cross-origin operation blocked',403)
        path=urlsplit(self.path).path
        try:
            body=self.read_body()
            if path=='/api/estimate':
                return self.respond({'estimate':pricing.estimate(body,database.rates(self.database_path))})
            if path=='/api/rates':
                return self.respond({'rates':database.change_rates(self.database_path,body)})
            if path=='/api/enquiries':
                enq=pricing.validate_enquiry(body)
                quote=pricing.estimate(enq['job'],database.rates(self.database_path))
                return self.respond({'enquiry':database.add(self.database_path,enq,quote)},201)
            found=re.fullmatch(r'/api/enquiries/(\d+)/(approve|reject)',path)
            if found:
                ident,action=int(found.group(1)),found.group(2)
                if action=='approve':
                    amount,note=pricing.validate_approval(body)
                else:
                    if set(body)!={'note'} or not isinstance(body['note'],str) or len(body['note'])>500:
                        raise pricing.InputError('Review note required, maximum 500 characters.')
                    amount,note=None,body['note'].strip()
                row,error=database.review(self.database_path,ident,'approved' if action=='approve' else 'rejected',amount,note)
                if error=='missing': return self.fail('Not found',404)
                if error: return self.fail('Already reviewed',409)
                return self.respond({'enquiry':row})
            return self.fail('Not found',404)
        except pricing.InputError as error:
            self.fail(str(error),400)
        except Exception:
            self.log_error('Request failure')
            self.fail('Internal server error',500)

def make_server(port=4173, db_path=DB_PATH):
    database.init(db_path)
    class LocalHandler(Handler): pass
    LocalHandler.database_path=db_path
    return ThreadingHTTPServer(('127.0.0.1',port),LocalHandler)

if __name__=='__main__':
    with make_server(int(os.environ.get('ONECALL_PORT','4173'))) as srv:
        print(f'Fictional ONECALL demo: http://127.0.0.1:{srv.server_port}/',flush=True)
        srv.serve_forever()
