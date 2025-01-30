import sqlite3 as sql


def criar_tabela_base_dados():
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    # Corrige a sintaxe da criação da tabela (incluindo parâmetros NULL e BOOL)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contato_clientes (
            numero_telefone TEXT PRIMARY KEY,
            token_de_conversa_chatgpt TEXT,
            ultima_mensagem TEXT NOT NULL,
            hora_ultima_mensagem INTEGER NULL,
            enviar_mensagem INTEGER NULL,
            mensagem_de_entrada TEXT NULL
        );
    ''')
    conexao.commit()  # Confirma a criação da tabela
    conexao.close()


def inserir_dados_novos_na_tabela(numero_telefone, token_conversa, mensagem, hora_mensagem, enviar_mensagem=0):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    cursor.execute('''
        INSERT INTO contato_clientes (
            numero_telefone,
            token_de_conversa_chatgpt,
            ultima_mensagem,
            hora_ultima_mensagem,
            enviar_mensagem
        )
        VALUES (?, ?, ?, ?, ?)
    ''', (numero_telefone, token_conversa, mensagem, hora_mensagem, enviar_mensagem))
    conexao.commit()
    conexao.close()


def atualizar_token_na_tabela(numero_telefone, token_conversa):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    # Usamos parâmetros ao invés de f-string
    cursor.execute('''
        UPDATE contato_clientes
        SET token_de_conversa_chatgpt = ?
        WHERE numero_telefone = ?;
    ''', (token_conversa, numero_telefone))
    conexao.commit()  # Confirma a atualização
    conexao.close()


def atualizar_hora_na_tabela(numero_telefone, hora_mensagem):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    cursor.execute('''
        UPDATE contato_clientes
        SET hora_ultima_mensagem = ?
        WHERE numero_telefone = ?;
    ''', (hora_mensagem, numero_telefone))
    conexao.commit()  # Confirma a atualização
    conexao.close()


def atualizar_mensagem(numero_telefone, mensagem):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    cursor.execute('''
        UPDATE contato_clientes
        SET ultima_mensagem = ?
        WHERE numero_telefone = ?;
    ''', (mensagem, numero_telefone))
    conexao.commit()
    conexao.close()

def atualizar_mensagem_de_entrada(numero_telefone, mensagem):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    cursor.execute('''
        UPDATE contato_clientes
        SET mensagem_de_entrada = ?
        WHERE numero_telefone = ?;
    ''', (mensagem, numero_telefone))
    conexao.commit()
    conexao.close()

def atualizar_permissao_de_envio(numero_telefone, permissao):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    cursor.execute('''
        UPDATE contato_clientes
        SET enviar_mensagem = ?
        WHERE numero_telefone = ?;
    ''', (permissao, numero_telefone))
    conexao.commit()
    conexao.close()

def puxar_dados(numero_cliente):
    conexao = sql.connect('clientes.db')
    cursor = conexao.cursor()
    # Retorna o registro correspondente (ou None, se não existir)
    cursor.execute('SELECT * FROM contato_clientes WHERE numero_telefone = ?', (numero_cliente,))
    dados = cursor.fetchone()
    conexao.close()
    return dados


# Exemplo de uso:
if __name__ == "__main__":
    criar_tabela_base_dados()

    # Insere dados de teste (note o 5º parâmetro para enviar_mensagem)
    # inserir_dados_novos_na_tabela("11999999999", "token_inicial", 'vai tomar no cu', 125451, 1)
    #
    # # Atualiza token
    # atualizar_token_na_tabela("11999999999", "token_alterado")
    #
    # # Atualiza hora
    # atualizar_hora_na_tabela("11999999999", 1234567890)

    # Busca dados
    resultado = puxar_dados("11999999999")
    print(resultado)
