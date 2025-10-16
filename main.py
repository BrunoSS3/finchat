import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

TELEGRAM_TOKEN =
GEMINI_API_KEY = 

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Saúda o usuário e informa a funcionalidade do Bot.
    """
    saudacao = (
        "Bem-vindo(a) ao Bot de Análise de Dados. \n"
        "Este sistema é projetado para processar dados textuais utilizando a API Gemini e "
        "retornar o resultado em formato JSON estruturado. \n"
        "Por favor, insira sua solicitação de análise."
    )
    await update.message.reply_text(saudacao)

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recebe o texto do usuário, envia para o Gemini com instrução de JSON
    e retorna o resultado processado ao Telegram.
    """
    user_text = update.message.text
    chat_id = update.message.chat_id

    await context.bot.send_message(chat_id, "Processando a solicitação. Por favor, aguarde.")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        system_prompt = (
            "Você é um Analista de Dados. Sua única e exclusiva resposta deve ser um bloco de código JSON VÁLIDO. "
            "A estrutura deve conter: {'tipo_analise': 'STRING', 'dados_chave': ['LISTA_DE_STRINGS'], 'status_processamento': 'OK/FALHA'}"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_text],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        
        try:
            json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(json_str)

            resultado = (
                f"**Análise Concluída**\n"
                f"**Tipo de Análise:** `{data.get('tipo_analise', 'Não Especificado')}`\n"
                f"**Status:** `{data.get('status_processamento', 'FALHA')}`\n"
                f"**Dados Chave Identificados:** `{' | '.join(data.get('dados_chave', ['Nenhum']))}`\n\n"
                f"**JSON Completo:**\n```json\n{json.dumps(data, indent=2)}\n```"
            )
        except (json.JSONDecodeError, AttributeError) as e:
            resultado = (
                "**Erro de Formato de Dados:** A API retornou uma estrutura inválida.\n"
                f"Detalhes do Erro: {e}\nResposta Bruta: {response.text[:100]}..."
            )

        await context.bot.send_message(chat_id, resultado, parse_mode='Markdown')
        
    except Exception as e:
        await context.bot.send_message(
            chat_id, 
            f"**Erro de Sistema:** Não foi possível estabelecer conexão com o serviço de análise. Detalhes: {e}"
        )

def main():
    """
    Inicia o aplicativo do Bot Telegram e registra os Handlers.
    """
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    print("O Bot de Análise está ONLINE. Iniciando Polling.")
    application.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()