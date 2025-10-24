## Finchat — Bot de Análise de Despesas

Breve: este repositório contém um bot Telegram que analisa comprovantes (texto ou imagem) e gera um JSON estruturado com o lançamento financeiro, salvando em um banco MongoDB.

## Estrutura mínima
- `main.py` — código principal do bot (handler de mensagens, integração com API de geração de conteúdo e MongoDB).

## Requisitos (sistema)
- Python 3.10+ recomendado
- MongoDB (Atlas ou instância acessível)

## Dependências Python recomendadas
- python-dotenv
- pymongo
- python-telegram-bot
- google-genai (ou pacote equivalente que você usa para a API Gemini)

Sugestão: crie um virtualenv antes de instalar.

## Instalação (PowerShell)
Abra o PowerShell e execute (exemplo):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install python-dotenv pymongo python-telegram-bot google-genai
```

Observação: ajuste o nome do pacote `google-genai` se você estiver usando outra biblioteca para a API da Google Gemini.

## Variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
TELEGRAM_TOKEN=<seu_token_telegram>
GEMINI_API_KEY=<sua_api_key_gemini>
MONGO_URI=<sua_uri_mongo>
```

Exemplo rápido no PowerShell (temporário):

```powershell
$env:TELEGRAM_TOKEN='<token>';$env:GEMINI_API_KEY='<sua_api_key>';$env:MONGO_URI='<sua_mongo_uri>'
```

## Instalação do MongoDB e do driver pymongo (com suporte SRV)

Recomendado: usar MongoDB Atlas (serviço gerenciado) ou uma instância local do MongoDB.

- Se usar o Atlas, crie um cluster e gere a `MONGO_URI` no formato `mongodb+srv://<user>:<pass>@cluster0.abcd.mongodb.net/<db>?retryWrites=true&w=majority`.
- Para que a string `mongodb+srv://` funcione, instale o driver com suporte a SRV (ele traz a dependência `dnspython` automaticamente):

```powershell
python -m pip install "pymongo[srv]"
```

Ou, no virtualenv já criado:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install "pymongo[srv]"
```

Se preferir manter tudo em `requirements.txt`, você pode substituir a linha de `pymongo` por:

```
pymongo[srv]>=4.3.0
```

Notas:
- Se usar Atlas, autorize seu IP (ou use 0.0.0.0/0 temporariamente durante desenvolvimento) no Network Access do Atlas.
- Para desenvolvimento local, instale o MongoDB Community Server (https://www.mongodb.com/try/download/community) e use a URI `mongodb://localhost:27017`.


## Como rodar
Com o ambiente ativado e as variáveis configuradas:

```powershell
python main.py
```

O bot usa polling por padrão (ver `application.run_polling`).

## Notas sobre alterações recentes
- Removi linguagem ofensiva e tornei mensagens ao usuário mais neutras e profissionais no arquivo `main.py`.
- Foram também normalizados alguns nomes de variáveis e campos do banco (ex.: `senha`, `telegram_id`, `valor`). Essas mudanças visam legibilidade e respeito.

Se você depender de campos antigos no banco de dados, revise os documentos existentes e faça migração/renomeação conforme necessário.

## Troubleshooting
- Erros de importação? Instale as dependências conforme a seção de instalação.
- Erro de conexão com o MongoDB? Verifique se `MONGO_URI` está correto e que seu IP/cluster permite conexões.

## Próximos passos (opcionais)
- Adicionar `requirements.txt` para travar dependências.
- Adicionar instruções de deploy (Docker/Heroku/Azure).
- Escrever testes unitários para os parseadores e fluxo de mensagens.

---
Se quiser que eu adicione o `requirements.txt` agora ou que eu gere um script de migração para atualizar documentos antigos do Mongo, me diga qual opção prefere.
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
