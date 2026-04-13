from http.server import HTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.error, os, base64, secrets, time

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

# Session store: {session_token: {email, expires_at}}
sessions = {}
SESSION_DURATION = 60 * 60 * 12  # 12 horas

def verify_google_token(token):
    if not token:
        return None
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        if data.get("aud") != GOOGLE_CLIENT_ID:
            return None
        email = data.get("email", "")
        return email if email in ALLOWED_EMAILS else None
    except:
        # Fallback: decode JWT payload
        try:
            parts = token.split('.')
            payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload))
            email = data.get("email", "")
            if data.get("aud") == GOOGLE_CLIENT_ID and email in ALLOWED_EMAILS:
                return email
        except:
            pass
        return None

def create_session(email):
    token = secrets.token_hex(32)
    sessions[token] = {'email': email, 'expires_at': time.time() + SESSION_DURATION}
    return token

def verify_session(token):
    if not token or token not in sessions:
        return None
    session = sessions[token]
    if time.time() > session['expires_at']:
        del sessions[token]
        return None
    # Renew session on each use
    session['expires_at'] = time.time() + SESSION_DURATION
    return session['email']

class OmieProxy(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.strip('/')

        # Login: verify Google token and return session token
        if path == 'auth/verify':
            try:
                data = json.loads(body)
                email = verify_google_token(data.get('token', ''))
                if email:
                    session_token = create_session(email)
                    self._respond(200, {'ok': True, 'email': email, 'session': session_token})
                else:
                    self._respond(200, {'ok': False, 'error': 'E-mail não autorizado'})
            except Exception as e:
                self._respond(200, {'ok': False, 'error': str(e)})
            return

        # Omie data: verify session token
        if path == 'omie/data':
            auth = self.headers.get('X-Auth-Token', '')
            email = verify_session(auth)
            if not email:
                self._respond(200, {'faultstring': 'Sessão expirada. Faça login novamente.'})
                return
            try:
                data = json.loads(body)
                payload = {
                    'call': data.get('call', ''),
                    'app_key': OMIE_KEY,
                    'app_secret': OMIE_SECRET,
                    'param': [data.get('param', {})]
                }
                url = f"https://app.omie.com.br/api/v1/{data.get('endpoint', '')}/"
                req = urllib.request.Request(url,
                    data=json.dumps(payload).encode(),
                    headers={'Content-Type': 'application/json'},
                    method='POST')
                with urllib.request.urlopen(req, timeout=15) as r:
                    self.send_response(200)
                    self._cors()
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(r.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self._respond(500, {'erro': str(e)})
            return

        self._respond(404, {'error': 'not found'})

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

print(f"Servidor na porta {PORT} | OMIE_KEY: {'OK' if OMIE_KEY else 'FALTANDO'}")
HTTPServer(('', PORT), OmieProxy).serve_forever()
