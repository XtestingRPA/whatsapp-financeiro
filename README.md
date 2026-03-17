
# 💬 WhatsApp Financeiro

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-green)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

Aplicativo desktop em **Python + Tkinter + SQLite** com interface inspirada em chat, focado em **registro, consulta, edição, exportação e envio de informações financeiras** usando **linguagem natural**.

Exemplos:

```text
Paguei 35 de gasolina hoje
Recebi 1200 de salário
Resumo março
Listar transferencias
Editar lancamento 12 valor 89.90
Exportar resumo pdf
Enviar relatorio xml para email@dominio.com
````

---

# 🚀 Visão Geral

O **WhatsApp Financeiro** funciona como um **assistente financeiro local**, com:

* interface estilo conversa
* persistência local em SQLite
* parser de linguagem natural
* categorização automática
* consultas por período
* edição de lançamentos
* exportação em XML e PDF
* envio por email
* relatórios detalhados
* suporte opcional a voz

Tudo roda localmente, sem precisar de backend externo para salvar dados.

---

# ✨ Features

## 🧾 Registro de lançamentos por linguagem natural

O sistema entende frases como:

```text
Paguei 35 de gasolina hoje
Gastei 80 em mercado dia 05/03
Recebi 40 de pix da Carlinha
Recebi 2500 de aposentadoria
Recebi 900 de aluguel
```

Campos extraídos automaticamente:

* data
* hora
* descrição
* valor
* tipo (`pago` ou `recebido`)
* categoria
* mensagem original

---

## 📊 Consultas de resumo

Permite obter:

* total pago
* total recebido
* saldo
* resumo por categoria
* período aplicado na consulta

Exemplos:

```text
Resumo este mês
Resumo março
Resumo do ano
Resumo de ano 2026
Resumo últimos 45 dias
Resumo última semana
Resumo semana passada
```

Exemplo de resposta:

```text
📊 Resumo última semana:
Período aplicado: 05/03/2026 a 11/03/2026
Total pago: R$ 373.00
Total recebido: R$ 3603.00
Saldo: R$ 3230.00
```

---

## 📋 Listagem de lançamentos

Permite listar lançamentos individuais com filtros.

Exemplos:

```text
listar março
listar transferencias
listar recebidos março
listar pagos fevereiro
listar combustivel
listar outros
listar ultimos
```

---

## 🏷️ Categorias dinâmicas

Além das categorias padrão, o app permite:

### Listar categorias

```text
listar categorias
```

### Criar nova categoria

```text
criar categoria Investimentos
```

### Criar categoria com palavras-chave

```text
criar categoria Curso com palavras curso,udemy,alura
```

As palavras-chave passam a ser usadas na categorização automática.

---

## ✏️ Edição de lançamentos

O sistema permite alterar lançamentos já salvos.

Exemplos:

```text
editar lancamento 12 valor 89.90
editar lancamento 12 descricao gasolina aditivada
editar lancamento 12 categoria Mercado
editar lancamento 12 tipo recebido
editar lancamento 12 data 2026-03-05
```

Campos editáveis:

* valor
* descrição
* categoria
* tipo
* data

---

## 📑 Relatórios completos

Além do resumo simples, o app pode gerar um **relatório mais completo** para um período ou filtro.

Exemplos:

```text
relatorio março
relatorio últimos 30 dias
relatorio combustivel últimos 30 dias
relatorio de janeiro até março
```

O relatório inclui:

* período usado
* total de lançamentos
* total pago
* total recebido
* saldo
* resumo por categoria
* amostra/listagem de lançamentos

---

## 📤 Exportação em XML e PDF

O app consegue salvar o último resumo ou relatório gerado em arquivo.

### Exportar resumo

```text
exportar resumo pdf
exportar resumo xml
```

### Exportar relatório

```text
exportar relatorio pdf
exportar relatorio xml
```

Arquivos são salvos na pasta:

```text
exports/
```

---

## 📧 Envio por email

Também é possível enviar por email o arquivo exportado.

### Enviar resumo

```text
enviar resumo pdf para email@dominio.com
enviar resumo xml para email@dominio.com
```

### Enviar relatório

```text
enviar relatorio pdf para email@dominio.com
enviar relatorio xml para email@dominio.com
```

---

## 📘 Ajuda melhorada

Agora o app possui ajuda organizada por tópico.

### Ajuda geral

```text
ajuda
```

### Ajuda por assunto

```text
ajuda categorias
ajuda editar
ajuda resumo
ajuda listar
ajuda relatorio
ajuda exportar
ajuda email
```

### Buscar ajuda

```text
buscar ajuda resumo
buscar ajuda categoria
buscar ajuda email
```

---

# 📆 Períodos suportados

O parser entende diversos formatos de período.

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
Listar de 23 de fevereiro a 6 de março
Resumo entre 23 de fevereiro e 6 de março
Resumo do dia 10/01 até 18/02
```

## Intervalo de meses

```text
Resumo de janeiro até março
Listar de novembro de 2025 até fevereiro de 2026
```

## Semana fixa dentro do mês

```text
Resumo primeira semana de janeiro
Resumo segunda semana de fevereiro
Listar terceira semana de março
Resumo última semana de abril
```

## Períodos relativos por dias

```text
Resumo últimos 7 dias
Resumo últimos 15 dias
Resumo últimos 30 dias
Resumo últimos 45 dias
```

Até:

* `365 dias`

## Períodos relativos por meses

```text
Resumo últimos 3 meses
Resumo últimos 6 meses
Resumo últimos 8 meses
Resumo últimos 12 meses
```

## Ano

```text
Resumo do ano
Resumo de ano 2025
Listar ano 2024
```

---

# 🗓️ Regras de semana

O sistema diferencia dois conceitos:

## Semana passada

Semana calendário anterior:

* segunda-feira até domingo da semana anterior

## Última semana

Últimos 7 dias reais, contando a partir de hoje.

Exemplo:

* `semana passada` = bloco fechado da semana anterior
* `última semana` = janela móvel de 7 dias

---

# 🧠 Categorização automática

Categorias padrão:

* Combustível
* Transferências
* Mercado
* Contas
* Renda
* Saúde
* Alimentação
* Transporte
* Outros

## Exemplos de classificação

| Palavra-chave | Categoria      |
| ------------- | -------------- |
| gasolina      | Combustível    |
| pix           | Transferências |
| salário       | Renda          |
| aluguel       | Renda          |
| aposentadoria | Renda          |
| remédio       | Saúde          |
| mercado       | Mercado        |
| uber          | Transporte     |

Se nenhuma regra for encontrada, o lançamento vai para:

* `Outros`

---

# 🎤 Suporte a voz

O app pode:

* reconhecer áudio do microfone
* transformar fala em texto
* responder com síntese de voz

Bibliotecas usadas:

* `SpeechRecognition`
* `pyttsx3`

Se microfone ou TTS não estiverem disponíveis, o app continua funcionando por texto.

---

# 🖥 Interface

Interface construída em **Tkinter**, com visual inspirado em aplicativos de mensagens.

Características:

* cabeçalho estilo chat
* histórico da conversa
* campo de mensagem
* botão de microfone
* botão de consulta
* mensagens organizadas por remetente

Dimensão atual:

```text
380x660
```

---

# 🗄 Banco de Dados

Banco local **SQLite**.

Arquivo principal:

```text
financeiro.db
```

---

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

### Campos

| Campo                | Tipo      | Descrição                   |
| -------------------- | --------- | --------------------------- |
| `id`                 | INTEGER   | identificador do lançamento |
| `data`               | TEXT      | data do lançamento          |
| `hora`               | TEXT      | hora do lançamento          |
| `descricao`          | TEXT      | descrição limpa             |
| `valor`              | REAL      | valor monetário             |
| `tipo`               | TEXT      | `pago` ou `recebido`        |
| `categoria`          | TEXT      | categoria do lançamento     |
| `mensagem_original`  | TEXT      | frase original enviada      |
| `data_hora_registro` | TIMESTAMP | momento do salvamento       |

---

## Tabela `categorias`

```sql
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    palavras_chave TEXT,
    criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Campos

| Campo            | Tipo      | Descrição                  |
| ---------------- | --------- | -------------------------- |
| `id`             | INTEGER   | identificador da categoria |
| `nome`           | TEXT      | nome da categoria          |
| `palavras_chave` | TEXT      | palavras-chave associadas  |
| `criada_em`      | TIMESTAMP | data de criação            |

---

## Índices criados

```text
idx_lancamentos_data
idx_lancamentos_categoria
idx_lancamentos_tipo
idx_lancamentos_descricao
```

---

# 📁 Estrutura sugerida do projeto

```text
whatsapp-financeiro/
│
├── app.py
├── financeiro.db
├── exports/
│   ├── resumo_*.pdf
│   ├── resumo_*.xml
│   ├── relatorio_*.pdf
│   └── relatorio_*.xml
├── requirements.txt
└── README.md
```

---

# 🛠 Dependências

## Bibliotecas padrão do Python

* `sqlite3`
* `re`
* `os`
* `smtplib`
* `unicodedata`
* `calendar`
* `pathlib`
* `datetime`
* `threading`
* `xml.etree.ElementTree`
* `email.message`

## Dependências externas

Instalação direta:

```bash
pip install SpeechRecognition python-dateutil pyttsx3 pyaudio reportlab
```

---

## `requirements.txt`

```txt
SpeechRecognition
python-dateutil
pyttsx3
PyAudio
reportlab
```

---

# ▶️ Como executar

## 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/whatsapp-financeiro.git
cd whatsapp-financeiro
```

## 2. Criar ambiente virtual

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## 4. Executar

```bash
python app.py
```

---

# ⚙️ Configuração de email

Para envio de email, configure estas variáveis de ambiente.

## Windows PowerShell

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="seu_email@gmail.com"
$env:SMTP_PASS="sua_senha_ou_app_password"
$env:SMTP_FROM="seu_email@gmail.com"
```

## Variáveis necessárias

* `SMTP_HOST`
* `SMTP_PORT`
* `SMTP_USER`
* `SMTP_PASS`
* `SMTP_FROM`

---

# 🧪 Exemplos de comandos

## Lançamentos

```text
Paguei 35 de gasolina hoje
Gastei 80 em mercado dia 05/03
Recebi 40 de pix da Carlinha
Recebi 2500 de aposentadoria
Recebi 900 de aluguel
```

## Resumos

```text
Resumo março
Resumo do ano
Resumo últimos 30 dias
Resumo semana passada
Resumo última semana
Resumo de janeiro até março
```

## Listagens

```text
listar março
listar transferencias
listar pagos fevereiro
listar recebidos março
listar outros
listar ultimos
```

## Categorias

```text
listar categorias
criar categoria Investimentos
criar categoria Curso com palavras curso,udemy,alura
```

## Edição

```text
editar lancamento 12 valor 89.90
editar lancamento 12 descricao gasolina aditivada
editar lancamento 12 categoria Mercado
editar lancamento 12 tipo recebido
editar lancamento 12 data 2026-03-05
```

## Relatórios

```text
relatorio março
relatorio últimos 30 dias
relatorio combustivel últimos 30 dias
relatorio de janeiro até março
```

## Exportação

```text
exportar resumo pdf
exportar resumo xml
exportar relatorio pdf
exportar relatorio xml
```

## Email

```text
enviar resumo pdf para email@dominio.com
enviar resumo xml para email@dominio.com
enviar relatorio pdf para email@dominio.com
enviar relatorio xml para email@dominio.com
```

## Ajuda

```text
ajuda
ajuda categorias
ajuda editar
ajuda relatorio
buscar ajuda resumo
buscar ajuda email
```

---

