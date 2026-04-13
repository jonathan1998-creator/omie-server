from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import urllib.request
import json

app = Flask(__name__)
CORS(app) 

PORT = int(os.environ.get('PORT', 8080))

@app.route('/omie/data', methods=['POST'])
def omie_proxy():
    # Recebe tudo do frontend (incluindo as chaves que você digitou)
    data = request.json
    endpoint = data.get('endpoint')
    call = data.get('call')
    param = data.get('param', {})
    app_key = data.get('app_key')
    app_secret = data.get('app_secret')

    # Monta a requisição com as chaves recebidas na hora
    payload = {
        "call": call,
        "app_key": app_key,
        "app_secret": app_secret,
        "param": [param]
    }
    
    url = f"https://app.omie.com.br/api/v1/{endpoint}/"
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return jsonify(result), 200
            
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
