from http.server import HTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.error, os

PORT = int(os.environ.get('PORT', 8765))

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
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if data.get("aud") != GOOGLE_CLIENT_ID:
            return None
        email = data.get("email", "")
        if email in ALLOWED_EMAILS:
            return email
        return None
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

        # Auth verification endpoint
        if self.path.strip('/') == 'auth/verify':
            try:
                data = json.loads(body)
                token = data.get('token', '')
                email = verify_google_token(token)
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                if email:
                    self.wfile.write(json.dumps({'ok': True, 'email': email}).encode())
                else:
                    self.wfile.write(json.dumps({'ok': False, 'error': 'Acesso não autorizado'}).encode())
            except Exception as e:
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': False, 'error': str(e)}).encode())
            return

        # Verify auth token for all Omie API calls
        auth_header = self.headers.get('X-Auth-Token', '')
        if not auth_header or not verify_google_token(auth_header):
            self.send_response(401)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Não autorizado'}).encode())
            return

        # Proxy to Omie
        path = self.path.lstrip('/')
        url = f'https://app.omie.com.br/api/v1/{path}/'
        try:
            req = urllib.request.Request(url, data=body,
                headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(500)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'erro': str(e)}).encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Auth-Token')

    def log_message(self, fmt, *args):
        print(f"[Omie] {self.address_string()} -> {args[0]}")

print(f"Servidor rodando na porta {PORT}")
HTTPServer(('', PORT), OmieProxy).serve_forever()
