# FinChat — Bot Telegram com Gemini (Google GenAI)

Um bot simples para Telegram que envia mensagens para o modelo Gemini (Google GenAI) e tenta extrair uma resposta JSON. O projeto está escrito em Python e usa as bibliotecas `python-telegram-bot` e `google-genai`.

## Aviso importante — chaves de API (MUITO IMPORTANTE)

Este projeto exige duas chaves de API para funcionar:

- TELEGRAM_TOKEN: token do bot do Telegram (ex.: `123456:ABC-DEF...`).
- GEMINI_API_KEY: API key do Google Gemini / Google GenAI (ex.: `AIza...` ou outra chave fornecida pelo Google). 

Estas chaves NÃO devem ser comitadas no repositório. Insira-as em variáveis de ambiente ou em um arquivo local ignorado pelo git (ex.: `.env`) antes de executar o bot.

Exemplo inseguro (NÃO RECOMENDADO):

```py
# main.py
TELEGRAM_TOKEN = "<sua_telegram_token_aqui>"
GEMINI_API_KEY = "<sua_gemini_api_key_aqui>"
```

Recomendado: usar variáveis de ambiente ou um arquivo `.env` e carregá-las no `main.py`.

## Dependências

- Python 3.10+ (recomendado)
- pip

Bibliotecas Python necessárias:

- python-telegram-bot
- google-genai

Você pode instalar as dependências com:

```powershell
pip install python-telegram-bot google-genai
```

Se preferir, crie um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; pip install python-telegram-bot google-genai
```

## Como configurar

1. Crie um bot no Telegram e obtenha o `TELEGRAM_TOKEN` (via @BotFather).
2. Obtenha a chave `GEMINI_API_KEY` na sua conta Google / Console de APIs para acesso ao Gemini/GenAI.
3. Configure as variáveis de ambiente no seu sistema ou use um `.env` local (com cuidado):

No Windows (PowerShell) temporariamente para a sessão atual:

```powershell
$env:TELEGRAM_TOKEN = "<seu_token_telegram>"; $env:GEMINI_API_KEY = "<sua_gemini_api_key>"
```

Ou crie um arquivo `.env` e carregue no `main.py` (ex.: usando `python-dotenv`).

4. Edite `main.py` se quiser inserir as chaves diretamente (não recomendado).

## Como executar

No PowerShell, na pasta do projeto, execute:

```powershell
python main.py
```

O bot iniciará em polling e ficará online enquanto o terminal estiver aberto. Envie mensagens no chat com o bot e ele responderá tentando devolver JSON formatado.

## Comportamento esperado

- `/start`: envia mensagem de boas-vindas.
- Ao enviar qualquer texto, o bot encaminha o texto para o Gemini, que deve responder com um bloco JSON. O script tenta limpar trilhas de markdown (como ```json) e fazer parse para JSON.

## Possíveis erros e soluções

- Erro de autenticação/permissão: verifique se as chaves estão corretas e com permissões ativas.
- Resposta inválida do Gemini: o bot tenta limpar e analisar o texto; se falhar, ele mostrará a resposta bruta e o erro de parsing.
- Dependências ausentes: verifique instalações com `pip list`.

## Segurança e boas práticas

- Nunca commit suas chaves em repositórios públicos.
- Use variáveis de ambiente ou cofres de segredos para produção.
- Limite o acesso do bot a chats confiáveis quando em produção.

## Arquivos relevantes

- `main.py` — código principal do bot.