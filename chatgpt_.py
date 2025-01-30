import json
import time
import openai
from base_dados_sql import (
    criar_tabela_base_dados,
    puxar_dados,
    inserir_dados_novos_na_tabela,
    atualizar_token_na_tabela,
    atualizar_mensagem,
    atualizar_hora_na_tabela,
)

# Inicialize sua tabela (caso ainda não exista).
criar_tabela_base_dados()

# Configure sua chave da OpenAI (substitua pela sua)
openai.api_key = ""

def conversar_com_openai(numero_telefone: str, texto_usuario: str, modelo: str = "gpt-4o-mini") -> str:
    """
    Função que gerencia o histórico de conversa do usuário (identificado pelo 'numero_telefone').
    1. Puxa dados do BD.
    2. Se não houver registro, cria um novo com uma mensagem system inicial.
    3. Lê o histórico armazenado em 'token_de_conversa_chatgpt' (JSON), adiciona a mensagem do usuário,
       chama a API da OpenAI, obtém resposta, e salva de volta em JSON.
    4. Atualiza ultima_mensagem e hora_ultima_mensagem no BD.
    5. Retorna a resposta do assistant.
    """
    # Passo 1: Obter dados do BD para este número
    dados = puxar_dados(numero_telefone)

    # Se 'dados' for None, significa que não há registro para esse número_telefone
    if not dados:
        # Precisamos criar um registro inicial
        # Vamos colocar uma system message inicial no histórico.
        # Armazenamos esse histórico como JSON no campo 'token_de_conversa_chatgpt'.
        historico_inicial = [
            {
                "role": "system",
                "content": (
                    '''COLOQUE AQUI DENTRO O COMANDO DO SEU ASSISTENTE'''
                )
            }
        ]
        token_inicial_json = json.dumps(historico_inicial, ensure_ascii=False)

        # Inserimos no BD, usando a função definida no database.py
        # (numero_telefone, token_conversa, mensagem, hora_mensagem, enviar_mensagem=0)
        inserir_dados_novos_na_tabela(
            numero_telefone,
            token_inicial_json,
            mensagem="(início de conversa)",
            hora_mensagem=int(time.time()),  # timestamp atual
            enviar_mensagem=0
        )
        # Buscamos novamente para ter o registro recém-inserido
        dados = puxar_dados(numero_telefone)

    # A estrutura do retorno da função 'puxar_dados' é algo como:
    # (numero_telefone, token_de_conversa_chatgpt, ultima_mensagem, hora_ultima_mensagem, enviar_mensagem)
    # Precisamos apenas do token_de_conversa_chatgpt agora
    numero_bd = dados[0]
    token_json = dados[1]

    # Passo 2: Carregar o histórico armazenado no token_de_conversa_chatgpt
    try:
        historico = json.loads(token_json) if token_json else []
    except json.JSONDecodeError:
        # Se der algum erro de parse, podemos redefinir o histórico
        historico = []

    # Passo 3: Adicionar a mensagem do usuário ao histórico
    historico.append({"role": "user", "content": texto_usuario})

    # Passo 4: Chamar a API da OpenAI com esse histórico
    resposta = openai.ChatCompletion.create(
        model=modelo,
        messages=historico
    )

    # Pegar o conteúdo da resposta (role: "assistant")
    resposta_texto = resposta.choices[0].message["content"].strip()

    # Passo 5: Adicionar a resposta do assistente ao histórico
    historico.append({"role": "assistant", "content": resposta_texto})

    # Passo 6: Converter o histórico atualizado para JSON e armazenar novamente no BD
    novo_token_json = json.dumps(historico, ensure_ascii=False)

    # Atualiza o campo token_de_conversa_chatgpt no BD
    atualizar_token_na_tabela(numero_telefone, novo_token_json)

    # Opcionalmente, podemos atualizar "ultima_mensagem" e "hora_ultima_mensagem"
    atualizar_mensagem(numero_telefone, resposta_texto)
    atualizar_hora_na_tabela(numero_telefone, int(time.time()))

    # Por fim, retornamos o texto da resposta
    return resposta_texto


def analisar_texto(texto: str, modelo: str = "gpt-4") -> str:
    """
    Função que analisa um texto fornecido pelo usuário, utilizando a API da OpenAI.

    Args:
        texto (str): Texto a ser analisado.
        modelo (str): Modelo da OpenAI a ser utilizado (padrão: "gpt-4").

    Returns:
        str: Resultado da análise do texto.
    """
    resposta = openai.ChatCompletion.create(
        model=modelo,
        messages=[
            {"role": "system", "content": r"Sua missão é dividir um texto em uma quantidade Y de valores de forma que ela faça sentido.Você deve responder a mensagem apenas com os textos reestruturados separados por ';'.Você irá receber a mensagem no seguinte formato: 'Texto: ???? \n Quantidade de partes a serem divididas: ????'"},
            {"role": "user", "content": texto}
        ]
    )

    return resposta.choices[0].message["content"].strip()

if __name__ == "__main__":
    # Exemplo de uso simples no console
    print("Assistente iniciado. Digite 'sair' para encerrar.")

    # Telefone fictício para teste
    telefone_teste = "11999999999"

    while True:
        user_input = input("Você: ")
        if user_input.strip().lower() == "sair":
            print("Encerrando...")
            break

        resposta = conversar_com_openai(telefone_teste, user_input)
        print("Assistente:", resposta)
