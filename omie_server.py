from http.server import HTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.error

PORT = 8765

class OmieProxy(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        print(f"[Omie] {self.address_string()} → {args[0]}")

print(f"✓ Servidor rodando em http://localhost:{PORT}")
print("  Deixe esta janela aberta enquanto usa o dashboard.")
print("  Para parar: Ctrl + C")
HTTPServer(('', PORT), OmieProxy).serve_forever()
