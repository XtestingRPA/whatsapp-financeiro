# 💬 WhatsApp Financeiro / FinancesXTG

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-green)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-2AABEE)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Aplicativo financeiro em **Python** com:

- interface local em **Tkinter**
- motor financeiro desacoplado em **FinanceCore**
- integração inicial com **Telegram Bot**
- persistência local em **SQLite**
- consultas, relatórios, exportação e email

Bot provisório no Telegram:

**http://t.me/FinancesXTG_bot**

---

# 🚀 Visão Geral

O projeto começou como um app local estilo chat para registrar e consultar finanças em linguagem natural, e agora também possui uma integração inicial com Telegram.

A arquitetura atual possui três camadas principais:

- **FinanceCore** → motor principal de negócio
- **App Tkinter** → interface local
- **Telegram Bot** → canal online inicial

Isso prepara o sistema para futuros canais, como:

- WhatsApp
- API web
- painel administrativo
- webhook em produção

---

## Deploy atual

O bot Telegram está rodando via webhook em um Web Service no Render.

### Stack atual de produção
- Telegram Bot API
- FastAPI
- python-telegram-bot
- Render Web Service
- Render Postgres

### Persistência
Os dados dos usuários são armazenados em banco PostgreSQL via `DATABASE_URL`.

### Isolamento por usuário
Os lançamentos são separados por:
- canal
- usuario_id
- chat_id

Isso permite que cada usuário veja apenas seus próprios dados.

### Bot provisório no Telegram
http://t.me/FinancesXTG_bot

---

# ✨ Funcionalidades

## 🧾 Registro de lançamentos

Exemplos:

```text
Paguei 35 de gasolina hoje
Gastei 80 em mercado dia 05/03
Recebi 1200 de salário
Recebi 2500 de aposentadoria
Recebi 900 de aluguel
````

O sistema extrai:

* data
* hora
* descrição
* valor
* tipo
* categoria
* mensagem original

---

## 📊 Resumos financeiros

Exemplos:

```text
Resumo este mês
Resumo março
Resumo do ano
Resumo semana passada
Resumo última semana
Resumo últimos 45 dias
```

Inclui:

* total pago
* total recebido
* saldo
* resumo por categoria
* período aplicado

---

## 📋 Listagem de lançamentos

Exemplos:

```text
listar março
listar transferencias
listar recebidos março
listar pagos fevereiro
listar combustivel
listar ultimos
```

---

## 🏷️ Categorias dinâmicas

Exemplos:

```text
listar categorias
criar categoria Investimentos
criar categoria Curso com palavras curso,udemy,alura
```

---

## ✏️ Edição de lançamentos

Exemplos:

```text
editar lancamento 12 valor 89.90
editar lancamento 12 descricao gasolina aditivada
editar lancamento 12 categoria Mercado
editar lancamento 12 tipo recebido
editar lancamento 12 data 2026-03-05
```

---

## 📑 Relatórios completos

Exemplos:

```text
relatorio março
relatorio últimos 30 dias
relatorio combustivel últimos 30 dias
relatorio de janeiro até março
```

---

## 📤 Exportação

Suporte para:

* XML
* PDF

Exemplos:

```text
exportar resumo pdf
exportar resumo xml
exportar relatorio pdf
exportar relatorio xml
```

Arquivos são salvos localmente em:

```text
exports/
```

No Telegram, o arquivo é enviado diretamente ao usuário sem expor caminho local.

---

## 📧 Envio por email

Exemplos:

```text
enviar resumo pdf para email@dominio.com
enviar relatorio xml para email@dominio.com
```

---

## 📘 Ajuda por tópico

Exemplos:

```text
ajuda
ajuda categorias
ajuda editar
ajuda relatorio
buscar ajuda resumo
buscar ajuda email
```

---

# 🤖 Integração com Telegram

Bot provisório:

**[http://t.me/FinancesXTG_bot](http://t.me/FinancesXTG_bot)**

## Recursos atuais no Telegram

* `/start`
* `/ajuda`
* `/comandos`
* `/resumo`
* `/ultimos`
* `/categorias`
* `/relatorio`

Também aceita mensagens livres como:

```text
Paguei 35 de gasolina hoje
Resumo março
Exportar resumo pdf
Relatorio últimos 30 dias
```

## Ações rápidas

O bot possui botões para:

* resumo do mês
* listar últimos lançamentos
* listar categorias
* relatório do mês
* exportar resumo em PDF
* ajuda

---

# 🧠 Arquitetura

## Camadas do projeto

### `finance_core.py`

Motor principal do sistema.

Responsável por:

* parser de mensagens
* gravação no SQLite
* consultas
* relatórios
* exportações
* envio de email
* categorias
* edição de lançamentos

### `app.py`

Interface local em Tkinter.

### `telegram_bridge.py`

Ponte entre Telegram e `FinanceCore`.

### `bot_telegram.py`

Canal Telegram usando `python-telegram-bot`.

---

# 📆 Períodos suportados

## Por mês

```text
Resumo março
Listar fevereiro
Resumo janeiro de 2026
```

## Por data específica

```text
Quanto gastei dia 23/02
```

## Intervalo de datas

```text
Resumo de 23/02 a 06/03
Resumo do dia 10/01 até 18/02
```

## Intervalo de meses

```text
Resumo de janeiro até março
Listar de novembro de 2025 até fevereiro de 2026
```

## Semana fixa do mês

```text
Resumo primeira semana de janeiro
Resumo terceira semana de março
```

## Períodos relativos

```text
Resumo últimos 7 dias
Resumo últimos 15 dias
Resumo últimos 30 dias
Resumo últimos 45 dias
Resumo últimos 8 meses
```

## Ano

```text
Resumo do ano
Resumo de ano 2026
Listar ano 2024
```

---

# 🗓️ Regras de semana

## Semana passada

Semana calendário anterior.

## Última semana

Últimos 7 dias reais.

---

# 🗄 Banco de Dados

Arquivo principal:

```text
financeiro.db
```

## Tabela `lancamentos`

```sql
CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    hora TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    mensagem_original TEXT,
    data_hora_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Tabela `categorias`

```sql
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    palavras_chave TEXT,
    criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 📁 Estrutura atual sugerida

```text
whatsapp-financeiro/
│
├── app.py
├── finance_core.py
├── telegram_bridge.py
├── bot_telegram.py
├── financeiro.db
├── exports/
├── requirements.txt
├── README.md
└── docs/
    └── screenshots/
```

---

# 🛠 Dependências

## Principais

```txt
SpeechRecognition
python-dateutil
pyttsx3
PyAudio
reportlab
python-telegram-bot>=22.0
python-dotenv
```

---

# ▶️ Execução local

## App Tkinter

```bash
python app.py
```

## Bot Telegram

```bash
python bot_telegram.py
```

---

# ⚙️ Variáveis de ambiente

## Telegram

```powershell
$env:TELEGRAM_BOT_TOKEN="SEU_TOKEN"
$env:TELEGRAM_ALLOWED_CHAT_IDS="123456789"
```

## Email

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="seu_email@gmail.com"
$env:SMTP_PASS="sua_senha_ou_app_password"
$env:SMTP_FROM="seu_email@gmail.com"
```

---

# 🔧 Roadmap

* [x] app local em Tkinter
* [x] FinanceCore desacoplado
* [x] integração inicial com Telegram
* [x] comandos rápidos no Telegram
* [x] exportação PDF/XML
* [x] email com anexo
* [ ] paginação no Telegram
* [ ] inline keyboard contextual após resumos
* [ ] deploy em webhook
* [ ] painel web
* [ ] integração com WhatsApp
* [ ] empacotamento `.exe`

---
