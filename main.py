import os
import sys
import json
from dotenv import load_dotenv

# Load .env if present
load_dotenv()
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from io import BytesIO 

# Configurações Essenciais (carregadas de variáveis de ambiente/.env)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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

# 1. Função de Início (/start)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saudacao = (
        "Bem-vindo(a) ao Bot de Análise de Despesas em Geral. \n"
        "Envie uma fotografia de um comprovante fiscal ou insira a despesa em texto livre. \n"
        "O sistema processará a informação e retornará um objeto JSON estruturado."
    )
    await update.message.reply_text(saudacao)

# 2. Função de Processamento de Mensagem de Texto
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

# 3. Função de Processamento de Imagem
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

# 4. Função de Tratamento de Resposta (JSON)
async def handle_gemini_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response):
    """
    Função genérica para limpar, validar e formatar a saída JSON do Gemini.
    """
    chat_id = update.message.chat_id
    try:
        json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
        data = json.loads(json_str)

        resultado = (
            f"**Processamento Concluído**\n"
            f"**Tipo de Transação:** `{data.get('tipo_transacao', data.get('tipo_gasto', 'N/A'))}`\n"
            f"**Data:** `{data.get('data', 'N/A')}`\n"
            f"**Valor Total:** `R$ {data.get('valor_total', 'N/A')}`\n"
            f"**Categoria Sugerida:** `{data.get('categoria_sugerida', data.get('tipo_gasto', 'NÃO CLASSIFICADO'))}`\n"
            f"**Descrição:** `{data.get('descricao', data.get('descricao_curta', 'Sem Detalhe'))}`\n\n"
            f"**JSON Bruto:**\n```json\n{json.dumps(data, indent=2)}\n```"
        )
    except (json.JSONDecodeError, AttributeError) as e:
        resultado = (
            "**Erro de Estrutura:** A saída da API não é um JSON válido.\n"
            f"Detalhes do Erro: {e}\nResposta Inicial: {response.text[:100]}..."
        )

    await context.bot.send_message(chat_id, resultado, parse_mode='Markdown')


# ---- Novo: estado de conversação simples em memória ----
conversation_state = {}


def parse_value_from_text(text: str):
    # tenta extrair um número simples do texto (ex: '100', '100,50', '100 reais')
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

    # Se há um estado ativo para esse chat, trate a resposta no fluxo
    state = conversation_state.get(chat_id)
    if state:
        # state contém: etapa, valor, categoria, data, descricao
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
            # agora compilamos um prompt curto e chamamos o Gemini para enriquecer/validar
            prompt = f"Valor: {state.get('valor')}, Data: {state.get('data') or 'N/A'}, Categoria sugerida: {state.get('categoria') or 'N/A'}, Descrição: {state.get('descricao')}\nGere o JSON final conforme o formato especificado." 
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(system_instruction=state.get('system_prompt'))
            )
            await handle_gemini_response(update, context, response)
            # limpa estado
            conversation_state.pop(chat_id, None)
            return

    # se não havia estado, verifica se a mensagem contém apenas um valor e nada mais relevante
    val = parse_value_from_text(text)
    # heurística simples: se o texto tem um número e tem menos de 4 palavras, considere valor isolado
    if val is not None and len(text.split()) <= 4:
        # inicia fluxo de perguntas
        conversation_state[chat_id] = {
            'etapa': 'ask_category',
            'valor': val,
            'system_prompt': SYSTEM_PROMPT
        }
        await context.bot.send_message(chat_id, f"Entendi, você registrou R$ {val:.2f}. Qual categoria sugere para essa transação?")
        return

    # caso contrário, use o fluxo normal já existente
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

    print("Bot de Análise ONLINE. Iniciando polling...")
    application.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()