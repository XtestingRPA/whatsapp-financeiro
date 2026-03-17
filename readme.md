# WhatsApp Financeiro

Aplicativo desktop em **Python + Tkinter + SQLite** com interface inspirada em chat, focado em **registro e consulta de lançamentos financeiros por linguagem natural**.

O sistema permite registrar gastos e receitas digitando ou falando frases como:

- `Paguei 35 de gasolina hoje`
- `Recebi 1200 de salário`
- `Recebi 900 de aluguel`
- `Gastei 80 em mercado dia 05/03`

Além disso, também permite consultar resumos e listagens por período, categoria e tipo, por exemplo:

- `Resumo março`
- `Resumo semana passada`
- `Resumo última semana`
- `Resumo últimos 30 dias`
- `Listar transferencias`
- `Listar recebidos março`

---

## Visão geral

O **WhatsApp Financeiro** funciona como um mini assistente financeiro local, com:

- interface gráfica estilo conversa
- persistência local em banco **SQLite**
- cadastro de lançamentos por texto natural
- consultas por período
- categorização automática
- suporte opcional a voz:
  - reconhecimento de fala
  - resposta por voz

Tudo roda localmente, sem necessidade de API externa para persistência.

---

## Funcionalidades

### 1. Registro de lançamentos por linguagem natural

O app interpreta frases e salva os dados no banco.

Exemplos aceitos:

- `Paguei 35 de gasolina hoje`
- `Gastei 80 em mercado dia 05/03`
- `Recebi 40 de pix da Carlinha`
- `Recebi 2500 de aposentadoria`
- `Recebi 900 de aluguel`
- `Paguei 34 de remédios`
- `Gastei 23 de gasolina dia 21/02`

Campos extraídos automaticamente:

- data
- hora
- descrição
- valor
- tipo (`pago` ou `recebido`)
- categoria
- mensagem original

---

### 2. Consultas de resumo

O sistema calcula:

- total pago
- total recebido
- saldo
- totais por categoria

Exemplos:

- `Resumo este mês`
- `Resumo março`
- `Resumo fevereiro`
- `Resumo do ano`
- `Resumo de ano 2026`
- `Quanto gastei em fevereiro`
- `Quanto gastei de combustível mês passado`

---

### 3. Consultas de listagem

O sistema lista os lançamentos individuais filtrados.

Exemplos:

- `Listar março`
- `Listar transferencias`
- `Listar recebidos março`
- `Listar pagos fevereiro`
- `Listar outros`
- `Listar combustivel`
- `Listar ano 2024`
- `Listar ultimos`

---

### 4. Períodos suportados

O app consegue interpretar diversos tipos de período.

#### Por mês
- `Resumo março`
- `Listar fevereiro`
- `Resumo janeiro de 2026`

#### Por data específica
- `Quanto gastei dia 23/02`

#### Por intervalo de datas
- `Resumo de 23/02 a 06/03`
- `Listar de 23 de fevereiro a 6 de março`
- `Resumo entre 23 de fevereiro e 6 de março`
- `Resumo do dia 10/01 até 18/02`

#### Por intervalo de meses
- `Resumo de janeiro até março`
- `Listar de novembro de 2025 até fevereiro de 2026`

#### Por semana fixa dentro do mês
- `Resumo primeira semana de janeiro`
- `Resumo segunda semana de fevereiro`
- `Listar terceira semana de março`
- `Resumo última semana de abril`

#### Períodos relativos por dias
- `Resumo últimos 7 dias`
- `Resumo últimos 15 dias`
- `Resumo últimos 30 dias`
- `Resumo últimos 45 dias`
- até `365 dias`

#### Períodos relativos por meses
- `Resumo últimos 3 meses`
- `Resumo últimos 6 meses`
- `Resumo últimos 8 meses`
- até `12 meses`

#### Semana passada x última semana
O sistema diferencia:

- `semana passada` = **semana calendário anterior**, de segunda a domingo
- `última semana` = **últimos 7 dias reais**

Exemplo:
- se hoje for `11/03/2026`
- `semana passada` = `02/03/2026 a 08/03/2026`
- `última semana` = `05/03/2026 a 11/03/2026`

---

### 5. Categorização automática

O app tenta classificar automaticamente os lançamentos com base em palavras-chave.

Categorias atuais:

- **Combustível**
- **Transferências**
- **Mercado**
- **Contas**
- **Renda**
- **Saúde**
- **Alimentação**
- **Transporte**
- **Outros**

#### Exemplos de classificação

##### Combustível
- gasolina
- combustível
- diesel
- etanol
- álcool

##### Transferências
- pix
- transferência
- transferências

##### Renda
- salário
- freela
- aposentadoria
- aluguel

##### Saúde
- farmácia
- remédio
- remédios
- médico

##### Alimentação
- restaurante
- lanche
- ifood
- padaria

##### Transporte
- uber
- 99
- ônibus

##### Contas
- água
- luz
- energia
- internet

##### Mercado
- mercado
- supermercado

Caso nenhuma regra seja encontrada, o lançamento vai para:

- **Outros**

---

### 6. Correção automática de registros antigos

O projeto possui rotina para corrigir registros antigos com descrições ruins, como por exemplo:

- `gasolinadia/`
- `pagueide remedios`
- `de gasolina dia/`

Comando disponível:

- `corrigir lancamentos`

Também existe correção automática na inicialização para registros detectados como “sujos”.

---

### 7. Exibição do período aplicado

Nas consultas, o app mostra o intervalo real usado no filtro.

Exemplo:

- `Período aplicado: 02/03/2026 a 08/03/2026`

Isso ajuda a validar exatamente qual janela temporal foi usada na consulta.

---

### 8. Interface com voz

O app pode:

- reconhecer áudio do microfone
- transformar fala em texto
- processar o texto reconhecido
- responder com síntese de voz

Recursos usados:
- `speech_recognition`
- `pyttsx3`

Se microfone ou TTS não estiverem disponíveis, o app continua funcionando com texto.

---

## Interface

A interface foi construída em **Tkinter**, com visual inspirado em aplicativos de mensagens.

Características:

- layout tipo chat
- cabeçalho estilo WhatsApp
- campo de mensagem
- botão de envio/extração
- botão de consulta
- botão de microfone
- área com histórico da conversa

Configuração atual da janela:

- **380x660**

---

## Estrutura do banco de dados

O banco usado é **SQLite**, armazenado em:

```text
financeiro.db
````

### Tabela principal: `lancamentos`

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
)
```

### Campos

| Campo                | Tipo      | Descrição                         |
| -------------------- | --------- | --------------------------------- |
| `id`                 | INTEGER   | Identificador do lançamento       |
| `data`               | TEXT      | Data do lançamento (`YYYY-MM-DD`) |
| `hora`               | TEXT      | Hora do lançamento                |
| `descricao`          | TEXT      | Descrição limpa/extraída          |
| `valor`              | REAL      | Valor monetário                   |
| `tipo`               | TEXT      | `pago` ou `recebido`              |
| `categoria`          | TEXT      | Categoria classificada            |
| `mensagem_original`  | TEXT      | Frase original digitada/falada    |
| `data_hora_registro` | TIMESTAMP | Momento em que foi salvo no banco |

### Índices criados

* `idx_lancamentos_data`
* `idx_lancamentos_categoria`
* `idx_lancamentos_tipo`
* `idx_lancamentos_descricao`

Esses índices ajudam a melhorar a performance das consultas.

---

## Dependências

### Biblioteca padrão do Python

Estas já vêm com o Python:

* `sqlite3`
* `re`
* `unicodedata`
* `pathlib`
* `datetime`
* `calendar`
* `tkinter`
* `threading`

### Dependências externas

Instale com:

```bash
pip install SpeechRecognition python-dateutil pyttsx3 pyaudio
```

#### Pacotes usados

* `SpeechRecognition`
* `python-dateutil`
* `pyttsx3`
* `PyAudio`

> Observação: em alguns ambientes o `PyAudio` pode ser o pacote mais trabalhoso de instalar.

---

## Requisitos

* Python 3.10+ recomendado
* Sistema com suporte a Tkinter
* Microfone disponível para uso de voz
* Ambiente local com permissão para criar arquivo SQLite

---

## Como executar

### 1. Clonar o projeto

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

### 2. Criar ambiente virtual

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install SpeechRecognition python-dateutil pyttsx3 pyaudio
```

### 4. Executar

```bash
python app.py
```

---

## Exemplos de uso

### Lançamentos

```text
Paguei 35 de gasolina hoje
Gastei 80 em mercado dia 05/03
Recebi 40 de pix da Carlinha
Recebi 1200 de salário
Recebi 2500 de aposentadoria
Recebi 900 de aluguel
```

### Resumos

```text
Resumo este mês
Resumo março
Resumo do ano
Resumo de ano 2026
Resumo últimos 7 dias
Resumo última semana
Resumo semana passada
Resumo primeiros dias de janeiro
Resumo de 23/02 a 06/03
Resumo de janeiro até março
```

### Listagens

```text
Listar março
Listar transferencias
Listar recebidos março
Listar pagos fevereiro
Listar combustivel
Listar outros
Listar últimos 15 dias
Listar ano 2024
Listar ultimos
```

### Utilitários

```text
ajuda
corrigir lancamentos
```

---

## Comandos principais

| Comando                | Função                                              |
| ---------------------- | --------------------------------------------------- |
| `ajuda`                | Mostra comandos disponíveis                         |
| `listar ultimos`       | Lista os últimos lançamentos salvos                 |
| `corrigir lancamentos` | Corrige descrições/categorias antigas problemáticas |
| `resumo ...`           | Exibe resumo agregado                               |
| `listar ...`           | Exibe lançamentos individuais                       |

---

## Como o app decide se a frase é lançamento ou consulta

### Lançamento

Se detectar:

* verbo de ação financeira (`paguei`, `gastei`, `recebi`, etc.)
* valor numérico

então a frase tende a ser tratada como **novo lançamento**.

### Consulta

Se detectar palavras como:

* `resumo`
* `listar`
* `quanto`
* `qual`
* `últimos`
* `semana passada`
* `nomes de mês`
* `ano`
* `intervalos`

então tende a ser tratada como **consulta**.

---

## Regras de negócio importantes

### `semana passada`

Refere-se à **semana calendário anterior**, de segunda a domingo.

### `última semana`

Refere-se aos **últimos 7 dias reais**, contando a partir da data atual.

### `aluguel` e `aposentadoria`

Atualmente são classificados como:

* **tipo**: `recebido` quando a frase indicar entrada
* **categoria**: `Renda`

---

## Limitações atuais

* parser baseado em regras e expressões regulares
* ainda não possui edição/exclusão por chat
* ainda não possui exportação para Excel/PDF
* categorização depende de palavras-chave conhecidas
* frases muito ambíguas podem cair em `Outros`
* funcionamento de voz depende de microfone e bibliotecas do sistema

---


## Estrutura do projeto

```text
whatsapp-financeiro/
├── app.py
├── financeiro.db
├── README.md
└── requirements.txt
```

---

## Exemplo de `requirements.txt`

```txt
SpeechRecognition
python-dateutil
pyttsx3
PyAudio
```

---

