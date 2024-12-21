import os
import requests
import platform
import socket
import json
import subprocess
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Função para iniciar o Ngrok automaticamente
def start_ngrok():
    try:
        # Rodar o Ngrok como subprocesso
        ngrok_process = subprocess.Popen(['ngrok', 'http', '5000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Esperar um pouco até o Ngrok estabelecer a conexão
        for _ in range(5):
            line = ngrok_process.stdout.readline().decode("utf-8")
            if 'http' in line:
                if 'localhost' in line:
                    ngrok_url = line.split(' ')[1].strip()
                    return ngrok_url
        return None
    except Exception as e:
        print(f"Erro ao iniciar o Ngrok: {str(e)}")
        return None

# Função para rodar o Flask
def run_flask():
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

@app.route('/')
def index():
    # Renderizar a página inicial com um menu interativo
    return render_template('index.html')

@app.route('/capture-location', methods=['POST'])
def capture_location():
    # Receber a localização exata enviada pelo navegador
    data = request.get_json()
    if not data:
        return jsonify({"error": "Nenhum dado de localização recebido."}), 400

    # Obter informações adicionais via IP
    try:
        ip_info = requests.get('https://ipinfo.io/json').json()
    except Exception as e:
        ip_info = {"error": f"Erro ao obter IP e localização: {str(e)}"}

    # Combinar informações de geolocalização com informações do sistema
    system_info = {
        'Hostname': socket.gethostname(),
        'Sistema Operacional': platform.system(),
        'Versão do SO': platform.version(),
        'Arquitetura': platform.architecture()[0],
        'Processador': platform.processor(),
        'IP Externo': ip_info.get('ip', 'N/A'),
        'Cidade (IP)': ip_info.get('city', 'N/A'),
        'Região (IP)': ip_info.get('region', 'N/A'),
        'País (IP)': ip_info.get('country', 'N/A'),
        'Localização (Lat, Long, via Navegador)': f"{data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}",
        'Precisão (em metros)': data.get('accuracy', 'N/A'),
        'Organização': ip_info.get('org', 'N/A'),
    }

    # Exibir informações no terminal
    print("\n[INFORMAÇÕES COMPLETAS DO DISPOSITIVO]")
    print(json.dumps(system_info, indent=4, ensure_ascii=False))

    return jsonify({"message": "Localização recebida com sucesso!"}), 200

# Menu de opções para testes
@app.route('/menu', methods=['GET'])
def menu():
    return jsonify({
        "opções": [
            "1 - Teste Local (sem ngrok)",
            "2 - Teste Remoto (usar ngrok)"
        ]
    })

# Rota para iniciar o servidor com o tipo de teste selecionado
@app.route('/start-test', methods=['POST'])
def start_test():
    data = request.get_json()
    if not data or 'tipo' not in data:
        return jsonify({"error": "Tipo de teste não informado."}), 400

    tipo = data['tipo']

    if tipo == "local":
        print("Executando teste local...")
        # Apenas executa o servidor localmente
        run_flask()
        return jsonify({"message": "Teste local iniciado."}), 200
    elif tipo == "remoto":
        print("Executando teste remoto...")
        # Iniciar o ngrok para fornecer o link remoto
        ngrok_url = start_ngrok()
        if ngrok_url:
            return jsonify({"message": "Teste remoto iniciado.", "ngrok_url": ngrok_url}), 200
        else:
            return jsonify({"error": "Não foi possível iniciar o Ngrok."}), 500
    else:
        return jsonify({"error": "Tipo de teste inválido."}), 400

if __name__ == '__main__':
    # Iniciar o Flask sem mensagens de debug
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Inicializa o servidor e o Ngrok
    ngrok_url = start_ngrok()
    if ngrok_url:
        print(f"Servidor remoto iniciado! Acesse o servidor através do link: {ngrok_url}")
    else:
        print("Erro ao iniciar o Ngrok.")

    # Rodar o Flask
    run_flask()
