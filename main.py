import os
import telebot
import barcode
from barcode.writer import ImageWriter
import pandas as pd

bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

# Carregar a base de dados
df = pd.read_csv('database_bot.csv', delimiter=';')  # Substitua 'database_bot.csv' pelo caminho do seu arquivo CSV
df.columns = df.columns.str.strip()  # Remove espaços em branco ao redor dos nomes das colunas
df['CPF'] = df['CPF'].astype(str).str.strip().str.zfill(11)  # Remove espaços em branco, converte para string e adiciona zeros à esquerda
df['WMS'] = df['WMS'].astype(str).str.strip()  # Remove espaços em branco e converte para string

@bot.message_handler(commands=["acesso"])
def acesso(mensagem):
    texto = """
    Digite os 6 dígitos do seu acesso ou seu CPF (Caso não saiba procure o T.I)"""
    bot.send_message(mensagem.chat.id, texto)
    bot.register_next_step_handler(mensagem, processar_acesso)

def processar_acesso(mensagem):
    entrada = mensagem.text.strip()  # Remove espaços em branco ao redor da entrada
    print(f"Entrada recebida: {entrada}")  # Mensagem de depuração
    if len(entrada) == 6 and entrada.isdigit():
        acesso_completo = entrada
    elif len(entrada) == 11 and entrada.isdigit():
        # Buscar o número de acesso pelo CPF
        pessoa = df[df['CPF'] == entrada]
        print(f"Pessoa encontrada: {pessoa}")  # Mensagem de depuração
        if not pessoa.empty:
            acesso_completo = str(pessoa.iloc[0]['WMS']).split('.')[0]  # Remove qualquer .0 no final
            if not acesso_completo.isdigit():
                bot.send_message(mensagem.chat.id, "Código de acesso não encontrado. Por favor, insira um código de acesso válido ou procure o T.I.")
                resposta(mensagem)  # Volta para o menu de opções
                return
            print(f"Acesso completo gerado pelo CPF: {acesso_completo}")  # Mensagem de depuração
        else:
            bot.send_message(mensagem.chat.id, "CPF não encontrado. Por favor, insira um CPF válido.")
            resposta(mensagem)  # Volta para o menu de opções
            return
    else:
        bot.send_message(mensagem.chat.id, "Entrada inválida. Por favor, insira 6 dígitos ou um CPF válido.")
        resposta(mensagem)  # Volta para o menu de opções
        return

    if not acesso_completo:
        bot.send_message(mensagem.chat.id, "Código de acesso não encontrado. Por favor, insira um código de acesso válido.")
        resposta(mensagem)  # Volta para o menu de opções
        return

    # Adiciona zeros à esquerda para garantir que o código tenha 12 dígitos
    acesso_completo_com_zeros = acesso_completo.zfill(12)
    print(f"Acesso completo com zeros: {acesso_completo_com_zeros}")  # Mensagem de depuração
    EAN = barcode.get_barcode_class('ean13')
    writer = ImageWriter()
    writer.set_options({'module_width': 0.2, 'module_height': 15.0, 'font_size': 10, 'text_distance': 1.0})
    ean = EAN(acesso_completo_com_zeros, writer=writer)
    ean.save("codigo_acesso", text=acesso_completo)  # Define o texto exibido como o código sem zeros à esquerda
    try:
        with open("codigo_acesso.png", "rb") as barcode_file:
            bot.send_photo(mensagem.chat.id, barcode_file)
    except Exception as e:
        bot.send_message(mensagem.chat.id, f"Erro ao enviar o código de barras: {e}")
    finally:
        resposta(mensagem)  # Volta para o menu de opções

@bot.message_handler(commands=["senha"])
def senha(mensagem):
    texto = """
    Digite a senha que deseja gerar o código de barras"""
    bot.send_message(mensagem.chat.id, texto)
    bot.register_next_step_handler(mensagem, processar_senha)

def processar_senha(mensagem):
    senha = mensagem.text.strip()  # Remove espaços em branco ao redor da entrada
    print(f"Senha recebida: {senha}")  # Mensagem de depuração
    Code128 = barcode.get_barcode_class('code128')
    writer = ImageWriter()
    writer.set_options({'module_width': 0.2, 'module_height': 15.0, 'font_size': 10, 'text_distance': 1.0})
    ean = Code128(senha, writer=writer)
    ean.save("codigo_senha")
    try:
        with open("codigo_senha.png", "rb") as barcode_file:
            bot.send_photo(mensagem.chat.id, barcode_file)
    except Exception as e:
        bot.send_message(mensagem.chat.id, f"Erro ao enviar o código de barras: {e}")
    finally:
        resposta(mensagem)  # Volta para o menu de opções

def verificar(mensagem):
    return True

@bot.message_handler(func=verificar)
def resposta(mensagem):
    texto = """
    Clique a opção para continuar
    /acesso Gerar código de barras de acesso
    /senha Gerar código de barras de senha
    """
    bot.send_message(mensagem.chat.id, texto)

bot.polling()