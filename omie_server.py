from http.server import HTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.error, os

PORT = int(os.environ.get('PORT', 8765))
OMIE_KEY = os.environ.get('OMIE_KEY', '')
OMIE_SECRET = os.environ.get('OMIE_SECRET', '')

ALLOWED_EMAILS = [
    "mauro@ondigital.seg.br",
    "rubens@ondigital.seg.br",
    "andrey@ondigital.seg.br",
    "jonathan@ondigital.seg.br"
]

GOOGLE_CLIENT_ID = "359112436189-bempnilpn1vfj3p6qhobjjhcnhdjfjt4.apps.googleusercontent.com"

def verify_google_token(token):
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        if data.get("aud") != GOOGLE_CLIENT_ID:
            return None
        email = data.get("email", "")
        return email if email in ALLOWED_EMAILS else None
    except:
        return None

class OmieProxy(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.strip('/')

        # Auth verification endpoint
        if path == 'auth/verify':
            try:
                data = json.loads(body)
                email = verify_google_token(data.get('token', ''))
                self._respond(200, {'ok': bool(email), 'email': email or '', 'error': '' if email else 'Acesso não autorizado'})
            except Exception as e:
                self._respond(200, {'ok': False, 'error': str(e)})
            return

        # Omie data endpoint — uses credentials from environment
        if path == 'omie/data':
            auth_header = self.headers.get('X-Auth-Token', '')
            if not verify_google_token(auth_header):
                self._respond(401, {'error': 'Não autorizado'})
                return
            try:
                data = json.loads(body)
                endpoint = data.get('endpoint', '')
                call = data.get('call', '')
                param = data.get('param', {})
                payload = {
                    'call': call,
                    'app_key': OMIE_KEY,
                    'app_secret': OMIE_SECRET,
                    'param': [param]
                }
                url = f'https://app.omie.com.br/api/v1/{endpoint}/'
                req = urllib.request.Request(url,
                    data=json.dumps(payload).encode(),
                    headers={'Content-Type': 'application/json'},
                    method='POST')
                with urllib.request.urlopen(req, timeout=15) as r:
                    result = r.read()
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self._respond(500, {'erro': str(e)})
            return

        self._respond(404, {'error': 'Not found'})

    def _respond(self, code, data):
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Auth-Token')

    def log_message(self, fmt, *args):
        print(f"[Omie] {self.address_string()} -> {args[0]}")

print(f"Servidor rodando na porta {PORT}")
print(f"OMIE_KEY configurada: {'sim' if OMIE_KEY else 'NAO'}")
HTTPServer(('', PORT), OmieProxy).serve_forever()
