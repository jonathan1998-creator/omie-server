from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import urllib.request
import json

app = Flask(__name__)
# O CORS abaixo libera a comunicação com o seu site no Netlify automaticamente
CORS(app) 

PORT = int(os.environ.get('PORT', 8080))
OMIE_KEY = os.environ.get('OMIE_KEY', '')
OMIE_SECRET = os.environ.get('OMIE_SECRET', '')

@app.route('/omie/data', methods=['POST'])
def omie_proxy():
    # Recebe o pedido do Frontend
    data = request.json
    endpoint = data.get('endpoint')
    call = data.get('call')
    param = data.get('param', {})

    # Monta o pacote de dados para enviar ao Omie (usando as chaves do Railway)
    payload = {
        "call": call,
        "app_key": OMIE_KEY,
        "app_secret": OMIE_SECRET,
        "param": [param]
    }
    
    url = f"https://app.omie.com.br/api/v1/{endpoint}/"
    
    try:
        # Faz a requisição oficial para o Omie
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
