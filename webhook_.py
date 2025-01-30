import threading
import requests
import time
from flask import Flask, request, jsonify
from base_dados_sql import *
from chatgpt import *
from random import  random
app = Flask(__name__)

# =========================================================================
# 1. Configurações / Credenciais
# =========================================================================
# Substitua pelos seus dados:
ACCESS_TOKEN = "COLOQUE SEU TOKEN DO WHATSAPP AQUI"
PHONE_NUMBER_ID = "COLOQUE O ID DO TELEFONE QUE ESTÁ NA API DO WHATSAPP"
VERIFY_TOKEN = "CODIGO DE VERIFICAÇÃO DO TOKEN"

# =========================================================================
# 2. Estruturas de dados para gerenciar os timers e as mensagens pendentes
# =========================================================================

# "timers" guardará um Timer ativo por número. Ex.: timers["558599999999"] = <Timer object>
timers = {}

# =========================================================================
# 3. Função para enviar mensagem via WhatsApp Cloud API
# =========================================================================

def send_whatsapp_message(phone_number, text_message):
    """
    Envia uma mensagem de texto ao número especificado via WhatsApp Cloud API.
    phone_number: string no formato E.164 (ex: '558591604837')
    text_message: texto a ser enviado
    """
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "text": {
            "body": text_message,

        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print("Falha ao enviar a mensagem:", response.text)

    return response.json()


# =========================================================================
# 4. Função chamada quando expira o timer de 50s (sem novas mensagens)
# =========================================================================

def on_timer_expire(phone_number,mensagem_usuario):
    """
    Função que é executada quando se passam 50 segundos sem que chegue
    nenhuma nova mensagem desse phone_number.
    """
    print('enviando mensagem')
    dados_cliente = puxar_dados(phone_number)
    resposta_chatgpt = conversar_com_openai(phone_number,mensagem_usuario)
    atualizar_mensagem_de_entrada(phone_number, '')
    numero_aleatorio = random()
    if numero_aleatorio > 0.8:
        quant_resposta = 3
    elif numero_aleatorio > 0.5:
        quant_resposta = 2
    else:
        quant_resposta = 1
    resposta_separada = analisar_texto(f"Texto: {resposta_chatgpt} \n Quantidade de partes a serem divididas: {quant_resposta}")

    match quant_resposta:
        case 1:
            send_whatsapp_message(phone_number,resposta_separada)
        case 2:
            split_mensagens = resposta_separada.split(';')
            send_whatsapp_message(phone_number, split_mensagens[0])
            time.sleep(5)
            send_whatsapp_message(phone_number,split_mensagens[1])
        case 3:
            split_mensagens = resposta_separada.split(';')
            send_whatsapp_message(phone_number, split_mensagens[0])
            time.sleep(5)
            send_whatsapp_message(phone_number, split_mensagens[1])
            time.sleep(5)
            send_whatsapp_message(phone_number, split_mensagens[2])



# =========================================================================
# 5. Rota do Webhook para receber mensagens
# =========================================================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # -------------------------
        # Verificação do Webhook
        # -------------------------
        hub_mode = request.args.get("hub.mode")
        hub_challenge = request.args.get("hub.challenge")
        hub_verify_token = request.args.get("hub.verify_token")

        if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
            return hub_challenge, 200
        else:
            return "Token de verificação inválido", 403

    elif request.method == "POST":
        # -------------------------
        # Recebendo dados do WhatsApp Cloud API
        # -------------------------
        data = request.get_json()

        try:
            # Extrai o número do remetente (campo 'from')
            phone_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            # Extrai o texto enviado
            text_body = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            # Extrai o nome (opcional)
            hora_mensagem_recebida = data["entry"][0]["changes"][0]["value"]["messages"][0]["timestamp"]

            print(f"[{time.strftime('%H:%M:%S')}] Mensagem recebida de {phone_number} ({hora_mensagem_recebida}): {text_body}")

            dados_cliente = puxar_dados(phone_number)

            if dados_cliente == None:
                historico_inicial = [
                    {
                        "role": "system",
                        "content": (
                            '''COLOQUE O PROMPT DO SEU ASSISTENTE AQUI'''
                        )
                    }
                ]
                token_inicial_json = json.dumps(historico_inicial, ensure_ascii=False)

                # Inserimos no BD, usando a função definida no database.py
                # (numero_telefone, token_conversa, mensagem, hora_mensagem, enviar_mensagem=0)
                inserir_dados_novos_na_tabela(
                    phone_number,
                    token_inicial_json,
                    mensagem="(início de conversa)",
                    hora_mensagem=int(time.time()),  # timestamp atual
                    enviar_mensagem=0
                )


            # Se já existe um timer para esse número, vamos cancelar (resetar contagem)
            if phone_number in timers:
                timers[phone_number].cancel()
                mensagem_nova = dados_cliente[5] + "\n" + text_body
                atualizar_mensagem_de_entrada(phone_number,mensagem_nova)
            else:
                mensagem_nova = text_body

            # Agora criar um novo timer de 50s
            t = threading.Timer(10.0, on_timer_expire, args=[phone_number,mensagem_nova])
            # Armazenar no dicionário
            timers[phone_number] = t
            # Iniciar contagem
            t.start()

        except (KeyError, IndexError, TypeError) as e:
            print("Erro ao extrair dados do JSON:", e)

        return jsonify({"status": "ok"}), 200


# =========================================================================
# 6. Executar a aplicação Flask
# =========================================================================

if __name__ == "__main__":
    # Em produção, use Gunicorn/uWSGI + HTTPS
    app.run(debug=True, port=8000)
