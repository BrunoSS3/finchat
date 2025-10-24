import os
import sys
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from io import BytesIO 
from pymongo import MongoClient 
import datetime


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
    
try:
    client = MongoClient(MONGO_URI)
    db = client.Finchat
    usuarios_collection = db.usuarios
    lancamentos_collection = db.lancamentos
    print("--- Conectado no Mongo Atlas ---")
except Exception as e:
    print(f"NÃO DEU PRA CONECTAR O BOT NO MONGO: {e}")
    sys.exit(1)

SYSTEM_PROMPT = '''Você é um Analista de Dados Financeiros de alta precisão. Sua ÚNICA e EXCLUSIVA função é processar o conteúdo fornecido (seja texto livre, imagem, ou uma combinação) e retornar o resultado em um bloco de código JSON VÁLIDO.

A SUA RESPOSTA DEVE SER APENAS O BLOCO DE CÓDIGO JSON, SEM QUALQUER TEXTO INTRODUTÓRIO, EXPLICAÇÃO OU SAUDAÇÃO.

ESTRUTURA OBRIGATÓRIA (ADAPTE CONFORME A TRANSAÇÃO):

{
    "tipo_transacao": "GASTO/RECEITA",
    "data": "DD/MM/AAAA",
    "valor_total": "FLOAT",
    "categoria_sugerida": "ALIMENTACAO/MORADIA_ALUGUEL/TRANSPORTE/SAUDE/LAZER/SALARIO_RECEITA/OUTROS",
    "descricao": "STRING_CURTA_DA_TRANSACAO"
}
DIRETRIZES DE EXTRAÇÃO:

Analise o contexto para determinar tipo_transacao (Salário ou Renda Extra é RECEITA; Compras e Contas são GASTO).

A categoria_sugerida deve ser escolhida APENAS entre as opções fornecidas.

Priorize a extração de data e valor_total diretamente do comprovante fiscal (se for uma imagem) ou do texto do usuário (se for uma mensagem).'''

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saudacao = (
        "Bem-vindo(a) ao Bot de Análise de Despesas em Geral. \n"
        "Envie uma fotografia de um comprovante fiscal ou insira a despesa em texto livre. \n"
        "O sistema processará a informação e retornará um objeto JSON estruturado."
    )
    await update.message.reply_text(saudacao)

async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    await context.bot.send_message(chat_id, "Iniciando processamento textual...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        system_prompt = SYSTEM_PROMPT

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_text],
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )
        
        await handle_gemini_response(update, context, response)
        
    except Exception as e:
        await context.bot.send_message(
            chat_id, 
            f"Erro na comunicação com o serviço Gemini. Detalhes: {e}"
        )

async def senha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para definir a senha de acesso do usuário."""
    chat_id = str(update.message.chat_id)
    try:
        senha = context.args[0]

        if len(senha) < 4:
            await update.message.reply_text("Senha muito curta. Use pelo menos 4 dígitos. Ex: /senha 1234")
            return

        usuarios_collection.update_one(
            { "telegram_id": chat_id },
            { "$set": { "senha": senha, "telegram_id": chat_id } },
            upsert=True
        )

        await update.message.reply_text(
            f"Sua senha foi salva com sucesso: {senha}\n\n"
            f"IMPORTANTE: O seu identificador (login) é este número:\n\n"
            f"`{chat_id}`\n\n"
            f"Use este número e a senha para acessar o site.",
            parse_mode='Markdown'
        )

    except (IndexError, TypeError):
        await update.message.reply_text("Use: /senha SUA_SENHA (ex: /senha 1234)")

async def process_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    await context.bot.send_message(chat_id, "Iniciando análise visual do comprovante. Este processo pode demorar alguns instantes.")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        
        photo_bytes = BytesIO()
        await photo_file.download_to_memory(photo_bytes)
        photo_bytes.seek(0)
        
        client = genai.Client(api_key=GEMINI_API_KEY)

        system_prompt = SYSTEM_PROMPT

        image_part = types.Part.from_bytes(
            data=photo_bytes.read(),
            mime_type='image/jpeg' 
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part],
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )
        
        await handle_gemini_response(update, context, response)

    except Exception as e:
        await context.bot.send_message(
            chat_id, 
            f"Erro na análise visual ou conexão. Detalhes: {e}"
        )



async def handle_gemini_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response):
    """
    Função genérica para limpar, validar, SALVAR NO MONGO e formatar a saída.
    """
    chat_id = update.message.chat_id
    telegram_id_str = str(chat_id)
    
    try:
        json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
        data = json.loads(json_str)
        usuario = usuarios_collection.find_one_and_update(
            { "telegram_id": telegram_id_str },
            { "$setOnInsert": { 
                "telegram_id": telegram_id_str, 
                "data_captura": datetime.datetime.now(datetime.timezone.utc)
            }},
            upsert=True,
            return_document=True
        )

        try:
            valor = float(data.get('valor_total', 0))
        except ValueError:
            valor = 0.0

        if data.get('tipo_transacao') == 'GASTO' and valor > 0:
            valor = -valor

        novo_lancamento = {
            "id_usuario": usuario['_id'],
            "descricao": data.get('descricao', 'N/A'),
            "valor": valor,
            "categoria": data.get('categoria_sugerida', 'OUTROS'),
            "data_lancamento": datetime.datetime.now(datetime.timezone.utc)
        }

        lancamentos_collection.insert_one(novo_lancamento)

        await context.bot.send_message(chat_id, "Lançamento salvo no banco de dados.")
        
        resultado = (
             f"**Processamento Concluído**\n"
             f"**Tipo de Transação:** `{data.get('tipo_transacao', 'N/A')}`\n"

         )
        await context.bot.send_message(chat_id, resultado, parse_mode='Markdown')


    except (json.JSONDecodeError, AttributeError, Exception) as e:
        resultado = (
             "**Erro de Estrutura ou pra salvar no Cofre:**\n"
             f"Detalhes do Erro: {e}\nResposta Inicial: {response.text[:100]}..."
         )
        await context.bot.send_message(chat_id, resultado)

conversation_state = {}


def parse_value_from_text(text: str):
    import re
    m = re.search(r"(\d+[\.,]?\d*)", text)
    if not m:
        return None
    v = m.group(1).replace(',', '.')
    try:
        return float(v)
    except:
        return None


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler unificado para texto: detecta valores puros e inicia fluxo de follow-up."""
    chat_id = update.message.chat_id
    text = (update.message.text or "").strip()

    state = conversation_state.get(chat_id)
    if state:
        etapa = state.get('etapa')
        if etapa == 'ask_category':
            state['categoria'] = text
            state['etapa'] = 'ask_date'
            await context.bot.send_message(chat_id, 'Quando ocorreu a despesa? (DD/MM/AAAA ou deixe em branco)')
            return
        if etapa == 'ask_date':
            state['data'] = text
            state['etapa'] = 'ask_description'
            await context.bot.send_message(chat_id, 'Descreva rapidamente a transação (ex: almoço, Uber, mercado)')
            return
        if etapa == 'ask_description':
            state['descricao'] = text
            prompt = f"Valor: {state.get('valor')}, Data: {state.get('data') or 'N/A'}, Categoria sugerida: {state.get('categoria') or 'N/A'}, Descrição: {state.get('descricao')}\nGere o JSON final conforme o formato especificado." 
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(system_instruction=state.get('system_prompt'))
            )
            await handle_gemini_response(update, context, response)
            conversation_state.pop(chat_id, None)
            return

    val = parse_value_from_text(text)
    if val is not None and len(text.split()) <= 4:
        
        conversation_state[chat_id] = {
            'etapa': 'ask_category',
            'valor': val,
            'system_prompt': SYSTEM_PROMPT
        }
        await context.bot.send_message(chat_id, f"Entendi, você registrou R$ {val:.2f}. Qual categoria sugere para essa transação?")
        return

    await process_text_message(update, context)


def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Faltando configuração: defina as variáveis de ambiente TELEGRAM_TOKEN e GEMINI_API_KEY antes de iniciar o bot.")
        print("No PowerShell (temporário): $env:TELEGRAM_TOKEN='<token>'; $env:GEMINI_API_KEY='<sua_api_key>'")
        sys.exit(1)

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.PHOTO, process_photo_message))
    application.add_handler(CommandHandler("senha", senha_command))

    print("Bot de Análise ONLINE. Iniciando polling...")
    application.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()
