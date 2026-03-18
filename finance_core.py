from __future__ import annotations

import os
import re
import sqlite3
import smtplib
import unicodedata
import calendar
from pathlib import Path
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from xml.etree.ElementTree import Element, SubElement, ElementTree
from email.message import EmailMessage
from typing import Optional, List

from dateutil.relativedelta import relativedelta

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False


@dataclass
class CoreResponse:
    text: str
    file_paths: List[Path] = field(default_factory=list)


class FinanceCore:
    def __init__(self, base_dir: Optional[Path] = None, db_name: str = "financeiro.db"):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent)
        self.db_path = self.base_dir / db_name
        self.export_dir = self.base_dir / "exports"
        self.export_dir.mkdir(exist_ok=True)

        self.show_period_debug = True
        self.last_query_context = None

        self.meses = {
            "janeiro": 1,
            "fevereiro": 2,
            "marco": 3,
            "março": 3,
            "abril": 4,
            "maio": 5,
            "junho": 6,
            "julho": 7,
            "agosto": 8,
            "setembro": 9,
            "outubro": 10,
            "novembro": 11,
            "dezembro": 12,
        }

        self.meses_exibicao = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }

        self.ordinais_semana = {
            "primeira": 1,
            "segunda": 2,
            "terceira": 3,
            "quarta": 4,
            "quinta": 5,
            "ultima": 99,
            "última": 99,
        }

        self.default_categories = {
            "energia": "Contas",
            "gasolina": "Combustível",
            "combustivel": "Combustível",
            "diesel": "Combustível",
            "etanol": "Combustível",
            "alcool": "Combustível",
            "lanche": "Alimentação",
            "conta de luz": "Contas",
            "luz": "Contas",
            "pix": "Transferências",
            "transferencia": "Transferências",
            "transferencias": "Transferências",
            "transferência": "Transferências",
            "transferências": "Transferências",
            "mercado": "Mercado",
            "supermercado": "Mercado",
            "agua": "Contas",
            "água": "Contas",
            "internet": "Contas",
            "aluguel": "Renda",
            "aposentadoria": "Renda",
            "restaurante": "Alimentação",
            "uber": "Transporte",
            "99": "Transporte",
            "onibus": "Transporte",
            "ônibus": "Transporte",
            "salario": "Renda",
            "salário": "Renda",
            "freela": "Renda",
            "ifood": "Alimentação",
            "padaria": "Alimentação",
            "farmacia": "Saúde",
            "farmácia": "Saúde",
            "remedio": "Saúde",
            "remédios": "Saúde",
            "remedios": "Saúde",
            "remédio": "Saúde",
            "medico": "Saúde",
            "médico": "Saúde",
        }

        self.help_topics = {
            "geral": [
                "ajuda",
                "ajuda categorias",
                "ajuda editar",
                "ajuda relatorio",
                "ajuda email",
                "buscar ajuda resumo",
            ],
            "categorias": [
                "listar categorias",
                "criar categoria Investimentos",
                "criar categoria Curso com palavras curso,udemy,alura",
            ],
            "editar": [
                "editar lancamento 12 valor 89.90",
                "editar lancamento 12 categoria Mercado",
                "editar lancamento 12 descricao gasolina aditivada",
                "editar lancamento 12 data 2026-03-05",
                "editar lancamento 12 tipo recebido",
            ],
            "resumo": [
                "resumo março",
                "resumo semana passada",
                "resumo última semana",
                "resumo últimos 30 dias",
                "resumo do ano",
            ],
            "listar": [
                "listar março",
                "listar transferencias",
                "listar recebidos março",
                "listar pagos fevereiro",
            ],
            "exportar": [
                "exportar resumo pdf",
                "exportar resumo xml",
                "exportar relatorio pdf",
                "exportar relatorio xml",
            ],
            "email": [
                "enviar resumo pdf para email@dominio.com",
                "enviar relatorio xml para email@dominio.com",
            ],
            "relatorio": [
                "relatorio março",
                "relatorio de janeiro até março",
                "relatorio combustivel últimos 30 dias",
            ],
        }

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_database()
        self.load_category_maps()
        self.auto_fix_dirty_records_on_startup()

    # =========================================================
    # utilidades
    # =========================================================
    def normalize_text(self, text):
        if text is None:
            return ""
        text = str(text).strip().lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def format_date_br(self, dt):
        return dt.strftime("%d/%m/%Y")

    def period_debug_text(self, start_date, end_date):
        return f"Período aplicado: {self.format_date_br(start_date)} a {self.format_date_br(end_date)}"

    # =========================================================
    # banco
    # =========================================================
    def init_database(self):
        cur = self.conn.cursor()

        cur.execute("""
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
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                palavras_chave TEXT,
                criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos(data)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_categoria ON lancamentos(categoria)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_tipo ON lancamentos(tipo)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_descricao ON lancamentos(descricao)")

        self.conn.commit()
        self.seed_default_categories()

    def seed_default_categories(self):
        cur = self.conn.cursor()

        grouped = {}
        for keyword, category in self.default_categories.items():
            grouped.setdefault(category, set()).add(self.normalize_text(keyword))

        for categoria, palavras in grouped.items():
            palavras_str = ",".join(sorted(palavras))
            cur.execute("SELECT id, palavras_chave FROM categorias WHERE nome = ?", (categoria,))
            row = cur.fetchone()

            if row is None:
                cur.execute(
                    "INSERT INTO categorias (nome, palavras_chave) VALUES (?, ?)",
                    (categoria, palavras_str)
                )
            else:
                atuais = set()
                if row["palavras_chave"]:
                    atuais = {self.normalize_text(x) for x in row["palavras_chave"].split(",") if x.strip()}
                novas = sorted(atuais.union(palavras))
                cur.execute(
                    "UPDATE categorias SET palavras_chave = ? WHERE nome = ?",
                    (",".join(novas), categoria)
                )

        self.conn.commit()

    def load_category_maps(self):
        cur = self.conn.cursor()
        cur.execute("SELECT nome, palavras_chave FROM categorias ORDER BY nome")
        rows = cur.fetchall()

        self.category_keywords_to_name = {}
        self.category_aliases = {}

        for row in rows:
            nome = row["nome"]
            nome_norm = self.normalize_text(nome)
            self.category_aliases[nome_norm] = nome

            palavras = []
            if row["palavras_chave"]:
                palavras = [self.normalize_text(x) for x in row["palavras_chave"].split(",") if x.strip()]

            for p in palavras:
                self.category_keywords_to_name[p] = nome

    # =========================================================
    # help
    # =========================================================
    def show_help(self, topic=None):
        if not topic:
            txt = (
                "📘 AJUDA\n"
                "────────────────\n"
                "Tópicos disponíveis:\n"
                "• ajuda categorias\n"
                "• ajuda editar\n"
                "• ajuda resumo\n"
                "• ajuda listar\n"
                "• ajuda relatorio\n"
                "• ajuda exportar\n"
                "• ajuda email\n"
                "• buscar ajuda palavra\n\n"
                "Comandos rápidos:\n"
                "• listar categorias\n"
                "• criar categoria Investimentos\n"
                "• editar lancamento 12 valor 89.90\n"
                "• resumo março\n"
                "• relatorio últimos 30 dias\n"
                "• exportar resumo pdf\n"
                "• enviar resumo pdf para email@dominio.com"
            )
            return CoreResponse(txt)

        key = self.normalize_text(topic)
        found = None
        for k in self.help_topics:
            if self.normalize_text(k) == key:
                found = k
                break

        if not found:
            return CoreResponse(f"Nenhum tópico de ajuda encontrado para '{topic}'.")

        items = self.help_topics[found]
        txt = f"📘 AJUDA - {found.upper()}\n────────────────\n"
        for item in items:
            txt += f"• {item}\n"
        return CoreResponse(txt)

    def search_help(self, term):
        term_norm = self.normalize_text(term)
        results = []
        for topic, items in self.help_topics.items():
            if term_norm in self.normalize_text(topic):
                results.append((topic, f"Tópico: {topic}"))
            for item in items:
                if term_norm in self.normalize_text(item):
                    results.append((topic, item))

        if not results:
            return CoreResponse(f"Nenhum resultado encontrado para ajuda: '{term}'.")

        txt = f"🔎 Busca de ajuda por '{term}':\n"
        shown = set()
        for topic, item in results:
            key = (topic, item)
            if key in shown:
                continue
            shown.add(key)
            txt += f"• [{topic}] {item}\n"
        return CoreResponse(txt)

    # =========================================================
    # categorias
    # =========================================================
    def list_categories(self):
        cur = self.conn.cursor()
        cur.execute("SELECT nome, palavras_chave FROM categorias ORDER BY nome")
        rows = cur.fetchall()

        if not rows:
            return CoreResponse("Nenhuma categoria cadastrada.")

        txt = "🏷️ Categorias cadastradas:\n"
        for row in rows:
            palavras = row["palavras_chave"] or ""
            preview = ", ".join([x for x in palavras.split(",") if x][:6])
            if preview:
                txt += f"• {row['nome']} -> {preview}\n"
            else:
                txt += f"• {row['nome']}\n"
        return CoreResponse(txt)

    def create_category(self, nome, palavras_chave_raw=""):
        nome = nome.strip()
        if not nome:
            return CoreResponse("Nome da categoria inválido.")

        palavras = []
        if palavras_chave_raw:
            palavras = [self.normalize_text(x) for x in re.split(r"[;,]", palavras_chave_raw) if x.strip()]

        cur = self.conn.cursor()
        cur.execute("SELECT id FROM categorias WHERE lower(nome) = lower(?)", (nome,))
        exists = cur.fetchone()
        if exists:
            return CoreResponse(f"A categoria '{nome}' já existe.")

        cur.execute(
            "INSERT INTO categorias (nome, palavras_chave) VALUES (?, ?)",
            (nome, ",".join(palavras))
        )
        self.conn.commit()

        self.load_category_maps()
        if palavras:
            return CoreResponse(f"✅ Categoria criada: {nome} | palavras-chave: {', '.join(palavras)}")
        return CoreResponse(f"✅ Categoria criada: {nome}")

    # =========================================================
    # edição
    # =========================================================
    def launch_exists(self, launch_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM lancamentos WHERE id = ?", (launch_id,))
        return cur.fetchone()

    def edit_launch_value(self, launch_id, value):
        row = self.launch_exists(int(launch_id))
        if not row:
            return CoreResponse(f"Lançamento #{launch_id} não encontrado.")

        try:
            val = float(value.replace(",", "."))
        except ValueError:
            return CoreResponse("Valor inválido.")

        cur = self.conn.cursor()
        cur.execute("UPDATE lancamentos SET valor = ? WHERE id = ?", (val, launch_id))
        self.conn.commit()
        return CoreResponse(f"✅ Lançamento #{launch_id} atualizado: valor = R$ {val:.2f}")

    def edit_launch_description(self, launch_id, description):
        row = self.launch_exists(int(launch_id))
        if not row:
            return CoreResponse(f"Lançamento #{launch_id} não encontrado.")

        desc = description.strip()
        if not desc:
            return CoreResponse("Descrição inválida.")

        cur = self.conn.cursor()
        cur.execute("UPDATE lancamentos SET descricao = ? WHERE id = ?", (desc, launch_id))
        self.conn.commit()
        return CoreResponse(f"✅ Lançamento #{launch_id} atualizado: descrição = {desc}")

    def edit_launch_category(self, launch_id, category):
        row = self.launch_exists(int(launch_id))
        if not row:
            return CoreResponse(f"Lançamento #{launch_id} não encontrado.")

        cat_norm = self.normalize_text(category.strip())
        valid = None
        for alias_norm, original in self.category_aliases.items():
            if alias_norm == cat_norm:
                valid = original
                break

        if valid is None:
            return CoreResponse(f"Categoria '{category}' não existe. Use 'listar categorias'.")

        cur = self.conn.cursor()
        cur.execute("UPDATE lancamentos SET categoria = ? WHERE id = ?", (valid, launch_id))
        self.conn.commit()
        return CoreResponse(f"✅ Lançamento #{launch_id} atualizado: categoria = {valid}")

    def edit_launch_type(self, launch_id, launch_type):
        row = self.launch_exists(int(launch_id))
        if not row:
            return CoreResponse(f"Lançamento #{launch_id} não encontrado.")

        launch_type = self.normalize_text(launch_type)
        if launch_type not in {"pago", "recebido"}:
            return CoreResponse("Tipo inválido. Use pago ou recebido.")

        cur = self.conn.cursor()
        cur.execute("UPDATE lancamentos SET tipo = ? WHERE id = ?", (launch_type, launch_id))
        self.conn.commit()
        return CoreResponse(f"✅ Lançamento #{launch_id} atualizado: tipo = {launch_type}")

    def edit_launch_date(self, launch_id, dt):
        row = self.launch_exists(int(launch_id))
        if not row:
            return CoreResponse(f"Lançamento #{launch_id} não encontrado.")

        try:
            datetime.strptime(dt, "%Y-%m-%d")
        except ValueError:
            return CoreResponse("Data inválida. Use YYYY-MM-DD.")

        cur = self.conn.cursor()
        cur.execute("UPDATE lancamentos SET data = ? WHERE id = ?", (dt, launch_id))
        self.conn.commit()
        return CoreResponse(f"✅ Lançamento #{launch_id} atualizado: data = {dt}")

    # =========================================================
    # parser
    # =========================================================
    def looks_like_transaction(self, message):
        msg = self.normalize_text(message)
        transaction_verbs = ["paguei", "gastei", "comprei", "recebi", "ganhei", "depositaram", "entrou", "debitei"]
        has_verb = any(re.search(rf"\b{verb}\b", msg) for verb in transaction_verbs)
        has_value = self.extract_value(message) is not None
        return has_verb and has_value

    def is_query(self, message_norm):
        query_patterns = [
            r"\bquanto\b", r"\bqual\b", r"\bresumo\b", r"\bextrato\b", r"\bsaldo\b",
            r"\btotal\b", r"\bmostre\b", r"\bliste\b", r"\blistar\b", r"\bquais\b",
            r"\bentre\b", r"\bprimeira semana\b", r"\bsegunda semana\b", r"\bterceira semana\b",
            r"\bquarta semana\b", r"\bquinta semana\b", r"\bultima semana\b", r"\búltima semana\b",
            r"\bsemana passada\b", r"\bultimos \d+ dias\b", r"\búltimos \d+ dias\b",
            r"\bultimos \d+ meses\b", r"\búltimos \d+ meses\b", r"\bdo ano\b", r"\bano \d{4}\b",
        ]
        if any(re.search(p, message_norm) for p in query_patterns):
            return True

        if re.search(r"\b(gastos|despesas|receitas|recebimentos)\b", message_norm):
            return True

        if re.search(r"\bmes passado\b", message_norm):
            return True

        if re.search(r"\b(esse mes|este mes|hoje|ontem)\b", message_norm):
            return True

        if re.search(r"\b(?:dia\s+)?\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", message_norm) and not self.looks_like_transaction(message_norm):
            return True

        for mes in self.meses.keys():
            if re.search(rf"\b{self.normalize_text(mes)}\b", message_norm) and not self.looks_like_transaction(message_norm):
                return True

        for palavra in ["transferencias", "transferencia", "pix", "outros", "saude", "mercado", "combustivel", "contas", "renda", "alimentacao", "transporte", "recebidos", "pagos"]:
            if re.search(rf"\b{palavra}\b", message_norm) and not self.looks_like_transaction(message_norm):
                return True

        return False

    def detect_query_mode(self, message_norm):
        if re.search(r"\b(listar|liste|mostre|quais)\b", message_norm):
            return "list"
        return "summary"

    def parse_date_token(self, day_str, month_str, year_str=None, default_year=None):
        if default_year is None:
            default_year = date.today().year
        try:
            day = int(day_str)
            month = int(month_str) if month_str.isdigit() else self.meses.get(self.normalize_text(month_str))
            if month is None:
                return None
            year = int(year_str) if year_str else default_year
            if year < 100:
                year += 2000
            return date(year, month, day)
        except Exception:
            return None

    def extract_relative_days_period(self, message_norm):
        if re.search(r"\b(ultima semana|última semana)\b", message_norm):
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
            return {"start_date": start_date, "end_date": end_date, "label": "última semana"}

        m = re.search(r"\b(?:ultimos|últimos)\s+(\d{1,3})\s+dias\b", message_norm)
        if not m:
            return None

        qtd = int(m.group(1))
        if qtd < 1 or qtd > 365:
            return None

        end_date = date.today()
        start_date = end_date - timedelta(days=qtd - 1)
        return {"start_date": start_date, "end_date": end_date, "label": f"últimos {qtd} dias"}

    def extract_relative_months_period(self, message_norm):
        m = re.search(r"\b(?:ultimos|últimos)\s+(\d{1,2})\s+meses\b", message_norm)
        if not m:
            return None

        qtd = int(m.group(1))
        if qtd < 1 or qtd > 12:
            return None

        end_date = date.today()
        start_date = end_date - relativedelta(months=qtd) + timedelta(days=1)
        return {"start_date": start_date, "end_date": end_date, "label": f"últimos {qtd} meses"}

    def extract_last_week_period(self, message_norm):
        if "semana passada" not in message_norm:
            return None

        today = date.today()
        start_of_current_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_current_week - timedelta(days=7)
        end_of_last_week = start_of_current_week - timedelta(days=1)

        return {"start_date": start_of_last_week, "end_date": end_of_last_week, "label": "semana passada"}

    def extract_year_period(self, message_norm):
        today = date.today()

        if re.search(r"\bdo ano\b", message_norm):
            return {"start_date": date(today.year, 1, 1), "end_date": date(today.year, 12, 31), "label": f"ano de {today.year}"}

        m = re.search(r"\bano\s+(\d{4})\b", message_norm)
        if m:
            ano = int(m.group(1))
            return {"start_date": date(ano, 1, 1), "end_date": date(ano, 12, 31), "label": f"ano de {ano}"}
        return None

    def extract_week_period(self, message_norm):
        pattern = (
            r"\b(primeira|segunda|terceira|quarta|quinta|ultima|última)\s+semana\s+de\s+"
            r"(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"(?:\s+de\s+(\d{4}))?\b"
        )
        m = re.search(pattern, message_norm)
        if not m:
            return None

        ordinal_txt, mes_txt, ano_txt = m.groups()
        mes_num = self.meses[self.normalize_text(mes_txt)]
        ano = int(ano_txt) if ano_txt else date.today().year

        ultimo_dia_mes = calendar.monthrange(ano, mes_num)[1]
        ultimo_dia = date(ano, mes_num, ultimo_dia_mes)
        ordinal = self.ordinais_semana[self.normalize_text(ordinal_txt)]

        if ordinal == 99:
            start_day = max(1, ultimo_dia_mes - 6)
            return {
                "start_date": date(ano, mes_num, start_day),
                "end_date": ultimo_dia,
                "label": f"última semana de {self.meses_exibicao[mes_num]} de {ano}"
            }

        start_day = 1 + (ordinal - 1) * 7
        if start_day > ultimo_dia_mes:
            return None
        end_day = min(start_day + 6, ultimo_dia_mes)
        return {
            "start_date": date(ano, mes_num, start_day),
            "end_date": date(ano, mes_num, end_day),
            "label": f"{ordinal_txt} semana de {self.meses_exibicao[mes_num]} de {ano}"
        }

    def extract_range_period(self, message_norm):
        current_year = date.today().year

        pattern_numeric = (
            r"\b(?:de|entre|do dia)\s+(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?"
            r"\s+(?:a|ate|até|e)\s+"
            r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b"
        )
        m = re.search(pattern_numeric, message_norm)
        if m:
            d1, m1, y1, d2, m2, y2 = m.groups()
            start_date = self.parse_date_token(d1, m1, y1, current_year)
            end_date = self.parse_date_token(d2, m2, y2, current_year)
            if start_date and end_date:
                if end_date < start_date:
                    start_date, end_date = end_date, start_date
                return {
                    "start_date": start_date,
                    "end_date": end_date,
                    "label": f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
                }
        return None

    def extract_month_range_period(self, message_norm):
        pattern = (
            r"\bde\s+"
            r"(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"(?:\s+de\s+(\d{4}))?"
            r"\s+(?:a|ate|até)\s+"
            r"(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"(?:\s+de\s+(\d{4}))?\b"
        )
        m = re.search(pattern, message_norm)
        if not m:
            return None

        mes1_txt, ano1_txt, mes2_txt, ano2_txt = m.groups()
        ano_atual = date.today().year
        mes1 = self.meses[self.normalize_text(mes1_txt)]
        mes2 = self.meses[self.normalize_text(mes2_txt)]
        ano1 = int(ano1_txt) if ano1_txt else ano_atual
        ano2 = int(ano2_txt) if ano2_txt else ano1

        start_date = date(ano1, mes1, 1)
        end_date = date(ano2, mes2, calendar.monthrange(ano2, mes2)[1])

        if end_date < start_date:
            start_date, end_date = end_date, start_date

        return {
            "start_date": start_date,
            "end_date": end_date,
            "label": f"{self.meses_exibicao[start_date.month]} de {start_date.year} até {self.meses_exibicao[end_date.month]} de {end_date.year}"
        }

    def extract_query_period(self, message_norm):
        today = date.today()

        for extractor in [
            self.extract_relative_days_period,
            self.extract_relative_months_period,
            self.extract_last_week_period,
            self.extract_year_period,
            self.extract_range_period,
            self.extract_month_range_period,
            self.extract_week_period,
        ]:
            result = extractor(message_norm)
            if result:
                return result

        date_specific = self.extract_specific_date_from_text(message_norm)
        if date_specific:
            return {"start_date": date_specific, "end_date": date_specific, "label": date_specific.strftime("%d/%m/%Y")}

        for mes_nome, mes_num in self.meses.items():
            mes_norm = self.normalize_text(mes_nome)
            if re.search(rf"\b{mes_norm}\b", message_norm):
                ano = today.year
                ano_match = re.search(rf"\b{mes_norm}\s+de\s+(\d{{4}})\b", message_norm)
                if ano_match:
                    ano = int(ano_match.group(1))
                return {
                    "start_date": date(ano, mes_num, 1),
                    "end_date": date(ano, mes_num, calendar.monthrange(ano, mes_num)[1]),
                    "label": f"{self.meses_exibicao[mes_num]} de {ano}"
                }

        if "mes passado" in message_norm:
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - relativedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return {"start_date": first_day_last_month, "end_date": last_day_last_month, "label": "mês passado"}

        if "esse mes" in message_norm or "este mes" in message_norm:
            return {"start_date": today.replace(day=1), "end_date": today, "label": "este mês"}

        if "hoje" in message_norm:
            return {"start_date": today, "end_date": today, "label": "hoje"}

        if "ontem" in message_norm:
            y = today - relativedelta(days=1)
            return {"start_date": y, "end_date": y, "label": "ontem"}

        return {"start_date": today.replace(day=1), "end_date": today, "label": "este mês"}

    def extract_specific_date_from_text(self, text):
        m = re.search(r"\b(?:dia\s+)?(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
        if not m:
            return None
        day, month, year = m.groups()
        try:
            year = int(year) if year else date.today().year
            if year < 100:
                year += 2000
            return date(year, int(month), int(day))
        except ValueError:
            return None

    def detect_query_category(self, message_norm):
        for alias_norm, category in self.category_aliases.items():
            if re.search(rf"\b{re.escape(alias_norm)}\b", message_norm):
                return category

        for keyword, category in self.category_keywords_to_name.items():
            if re.search(rf"\b{re.escape(keyword)}\b", message_norm):
                return category

        return None

    def detect_query_type(self, message_norm):
        if any(word in message_norm for word in ["paguei", "gastei", "gasto", "despesa", "despesas", "pagos", "pago"]):
            return "pago"
        if any(word in message_norm for word in ["recebi", "receita", "receitas", "recebimento", "ganhei", "recebidos", "recebido"]):
            return "recebido"
        return None

    def detect_query_description_term(self, message_norm, query_mode):
        termos_ignorar = {
            "quanto", "gastei", "paguei", "recebi", "resumo", "extrato", "saldo", "total",
            "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
            "este", "esse", "mes", "mês", "passado", "passada", "hoje", "ontem", "dia",
            "com", "categoria", "reais", "real", "gastos", "despesas", "receitas",
            "janeiro", "fevereiro", "marco", "março", "abril", "maio", "junho", "julho",
            "agosto", "setembro", "outubro", "novembro", "dezembro",
            "listar", "liste", "mostre", "quais", "recebidos", "pagos",
            "primeira", "segunda", "terceira", "quarta", "quinta", "ultima", "última",
            "semana", "entre", "ate", "até", "a", "ultimos", "últimos", "dias", "meses", "ano",
            "buscar", "ajuda", "relatorio", "relatório", "exportar", "enviar", "pdf", "xml", "para",
        }

        for alias_norm in self.category_aliases.keys():
            termos_ignorar.add(alias_norm)
        for keyword in self.category_keywords_to_name.keys():
            termos_ignorar.add(keyword)

        if query_mode == "list":
            return None

        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", message_norm)
        candidatos = [t for t in tokens if t not in termos_ignorar]

        for token in candidatos:
            if re.fullmatch(r"\d{1,4}", token):
                continue
            return token
        return None

    # =========================================================
    # queries
    # =========================================================
    def fetch_query_rows(self, start_date, end_date, categoria=None, tipo=None, termo_descricao=None):
        query = "SELECT * FROM lancamentos WHERE date(data) BETWEEN ? AND ?"
        params = [start_date.isoformat(), end_date.isoformat()]

        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)

        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)

        if termo_descricao:
            query += " AND lower(descricao) LIKE ?"
            params.append(f"%{termo_descricao.lower()}%")

        query += " ORDER BY data DESC, hora DESC, id DESC"

        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def execute_summary_query(self, start_date, end_date, categoria, tipo, periodo_label, termo_descricao=None):
        resultados = self.fetch_query_rows(start_date, end_date, categoria, tipo, termo_descricao)

        if not resultados:
            detalhe = []
            if categoria:
                detalhe.append(f"categoria {categoria}")
            if tipo:
                detalhe.append(f"tipo {tipo}")
            if termo_descricao:
                detalhe.append(f"descrição contendo '{termo_descricao}'")

            complemento = f" com filtro de {' | '.join(detalhe)}" if detalhe else ""
            texto = f"Nenhum lançamento encontrado para {periodo_label}{complemento}."
            if self.show_period_debug:
                texto += f"\n{self.period_debug_text(start_date, end_date)}"
            return CoreResponse(texto)

        total_pago = sum(r["valor"] for r in resultados if r["tipo"] == "pago")
        total_recebido = sum(r["valor"] for r in resultados if r["tipo"] == "recebido")

        categorias = {}
        for r in resultados:
            cat = r["categoria"]
            categorias.setdefault(cat, {"pago": 0.0, "recebido": 0.0})
            categorias[cat][r["tipo"]] += r["valor"]

        response = f"📊 Resumo {periodo_label}:\n"
        if self.show_period_debug:
            response += f"{self.period_debug_text(start_date, end_date)}\n"
        response += f"Total pago: R$ {total_pago:.2f}\n"
        response += f"Total recebido: R$ {total_recebido:.2f}\n"
        response += f"Saldo: R$ {total_recebido - total_pago:.2f}\n\n"
        response += "Por categoria:\n"

        for cat, valores in categorias.items():
            if valores["pago"] > 0:
                response += f"• {cat}: R$ {valores['pago']:.2f} (pago)\n"
            if valores["recebido"] > 0:
                response += f"• {cat}: R$ {valores['recebido']:.2f} (recebido)\n"

        return CoreResponse(response)

    def execute_list_query(self, start_date, end_date, categoria, tipo, periodo_label, termo_descricao=None):
        rows = self.fetch_query_rows(start_date, end_date, categoria, tipo, termo_descricao)

        if not rows:
            detalhe = []
            if categoria:
                detalhe.append(categoria)
            if tipo:
                detalhe.append(tipo)
            if termo_descricao:
                detalhe.append(termo_descricao)

            complemento = f" ({' | '.join(detalhe)})" if detalhe else ""
            texto = f"Nenhum lançamento encontrado para {periodo_label}{complemento}."
            if self.show_period_debug:
                texto += f"\n{self.period_debug_text(start_date, end_date)}"
            return CoreResponse(texto)

        texto = f"📋 Lançamentos {periodo_label}:\n"
        if self.show_period_debug:
            texto += f"{self.period_debug_text(start_date, end_date)}\n"

        for row in rows[:30]:
            texto += (
                f"#{row['id']} | {row['data']} | {row['descricao']} | "
                f"R$ {row['valor']:.2f} | {row['tipo']} | {row['categoria']}\n"
            )

        if len(rows) > 30:
            texto += f"\n... e mais {len(rows) - 30} lançamento(s)."

        total_pago = sum(r["valor"] for r in rows if r["tipo"] == "pago")
        total_recebido = sum(r["valor"] for r in rows if r["tipo"] == "recebido")

        texto += "\n"
        texto += f"\nTotal pago: R$ {total_pago:.2f}"
        texto += f"\nTotal recebido: R$ {total_recebido:.2f}"
        texto += f"\nSaldo: R$ {total_recebido - total_pago:.2f}"

        return CoreResponse(texto)

    # =========================================================
    # lançamentos
    # =========================================================
    def extract_value(self, message):
        m = re.search(r"\b(?:r\$|rs)?\s*(\d+[.,]\d+|\d+)\s*(?:reais|r\$)?\b", message, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except ValueError:
                return None
        return None

    def determine_tipo_lancamento(self, message_norm):
        palavras_pago = ["paguei", "gastei", "comprei", "debitei", "despesa", "pago"]
        palavras_recebido = ["recebi", "ganhei", "entrou", "depositaram", "salario", "freela", "renda", "receita", "aposentadoria", "aluguel"]

        if any(re.search(rf"\b{p}\b", message_norm) for p in palavras_pago):
            return "pago"
        if any(re.search(rf"\b{p}\b", message_norm) for p in palavras_recebido):
            return "recebido"
        return "pago"

    def extract_description(self, message):
        texto = self.normalize_text(message)
        texto = re.sub(r"\b(?:r\$|rs)?\s*\d+[.,]?\d*\s*(?:reais|r\$)?\b", " ", texto)
        texto = re.sub(r"\b(?:dia\s+)?\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", " ", texto)
        texto = re.sub(r"\b(?:em\s+)?\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", " ", texto)
        texto = re.sub(r"\b(paguei|gastei|comprei|recebi|ganhei|entrou|depositaram|pagar|gastar|comprar|debitei)\b", " ", texto)

        for mes in self.meses.keys():
            texto = re.sub(rf"\b{self.normalize_text(mes)}\b", " ", texto)

        texto = re.sub(r"\b(hoje|ontem|amanha|mes|passado|este|esse|dia)\b", " ", texto)
        texto = re.sub(r"\b(de|do|da|dos|das|com|em|no|na|nos|nas)\b", " ", texto)
        texto = re.sub(r"[^a-z0-9\s]", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()

        if not texto:
            return "Lançamento"

        tokens = [t for t in texto.split() if t not in {"real", "reais"}]
        texto = " ".join(tokens).strip()
        return texto if texto else "Lançamento"

    def determine_category(self, message_norm):
        for keyword, category in self.category_keywords_to_name.items():
            if re.search(rf"\b{re.escape(keyword)}\b", message_norm):
                return category

        if any(x in message_norm for x in ["aposentadoria", "aluguel", "salario", "freela", "renda"]):
            return "Renda"

        return "Outros"

    def extract_date_time(self, message):
        today = datetime.now()
        msg = self.normalize_text(message)

        if "ontem" in msg:
            data = (today - relativedelta(days=1)).strftime("%Y-%m-%d")
        elif "amanha" in msg:
            data = (today + relativedelta(days=1)).strftime("%Y-%m-%d")
        elif "hoje" in msg:
            data = today.strftime("%Y-%m-%d")
        else:
            date_match = re.search(r"\b(?:dia\s+|em\s+)?(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", message, re.IGNORECASE)
            if date_match:
                day, month, year = date_match.groups()
                year = int(year) if year else today.year
                if year < 100:
                    year += 2000
                try:
                    data = f"{year:04d}-{int(month):02d}-{int(day):02d}"
                except ValueError:
                    data = today.strftime("%Y-%m-%d")
            else:
                data = today.strftime("%Y-%m-%d")

        return data, today.strftime("%H:%M:%S")

    def extract_lancamento(self, message):
        message_norm = self.normalize_text(message)
        valor = self.extract_value(message)
        if valor is None:
            return None

        tipo = self.determine_tipo_lancamento(message_norm)
        data, hora = self.extract_date_time(message)
        categoria = self.determine_category(message_norm)
        descricao = self.extract_description(message)

        return {
            "data": data,
            "hora": hora,
            "descricao": descricao,
            "valor": valor,
            "tipo": tipo,
            "categoria": categoria,
            "mensagem_original": message
        }

    def save_lancamento(self, lancamento):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO lancamentos
                (data, hora, descricao, valor, tipo, categoria, mensagem_original)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lancamento["data"], lancamento["hora"], lancamento["descricao"],
                lancamento["valor"], lancamento["tipo"], lancamento["categoria"],
                lancamento["mensagem_original"]
            ))
            self.conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================
    # correções
    # =========================================================
    def description_looks_dirty(self, descricao):
        desc = self.normalize_text(descricao)
        if not desc or len(desc) <= 2:
            return True

        dirty_patterns = [r"/", r"\b(pagueide|gasteide|gasolinadia)\b", r"\bdia\b", r"^\bde\b", r"\bde$"]
        return any(re.search(pattern, desc) for pattern in dirty_patterns)

    def rebuild_description_from_original(self, mensagem_original, descricao_atual):
        base_text = mensagem_original if mensagem_original else descricao_atual
        nova_descricao = self.extract_description(base_text)

        priority = [
            "gasolina", "combustivel", "etanol", "diesel", "pix", "transferencia",
            "aposentadoria", "aluguel", "remedios", "remedio", "farmacia", "medico",
            "uber", "mercado", "salario", "ifood", "padaria", "internet", "agua", "luz"
        ]

        texto_norm = self.normalize_text(base_text)
        for termo in priority:
            if termo in texto_norm:
                return termo

        return nova_descricao if nova_descricao else descricao_atual

    def recalculate_category_from_original(self, mensagem_original, descricao):
        base_text = f"{mensagem_original or ''} {descricao or ''}"
        return self.determine_category(self.normalize_text(base_text))

    def auto_fix_dirty_records_on_startup(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id, descricao, categoria, mensagem_original FROM lancamentos ORDER BY id ASC")
            rows = cur.fetchall()

            atualizados = 0

            for row in rows:
                descricao_atual = row["descricao"] or ""
                mensagem_original = row["mensagem_original"] or ""
                categoria_atual = row["categoria"] or "Outros"

                if not self.description_looks_dirty(descricao_atual):
                    continue

                nova_descricao = self.rebuild_description_from_original(mensagem_original, descricao_atual)
                nova_categoria = self.recalculate_category_from_original(mensagem_original, nova_descricao)

                if nova_descricao != descricao_atual or nova_categoria != categoria_atual:
                    cur.execute(
                        "UPDATE lancamentos SET descricao = ?, categoria = ? WHERE id = ?",
                        (nova_descricao, nova_categoria, row["id"])
                    )
                    atualizados += 1

            self.conn.commit()
            return atualizados
        except Exception:
            return 0

    def run_manual_fix_dirty_records(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id, descricao, categoria, mensagem_original FROM lancamentos ORDER BY id ASC")
            rows = cur.fetchall()

            atualizados = 0
            detalhes = []

            for row in rows:
                descricao_atual = row["descricao"] or ""
                mensagem_original = row["mensagem_original"] or ""
                categoria_atual = row["categoria"] or "Outros"

                nova_descricao = self.rebuild_description_from_original(mensagem_original, descricao_atual)
                nova_categoria = self.recalculate_category_from_original(mensagem_original, nova_descricao)

                if nova_descricao != descricao_atual or nova_categoria != categoria_atual:
                    cur.execute(
                        "UPDATE lancamentos SET descricao = ?, categoria = ? WHERE id = ?",
                        (nova_descricao, nova_categoria, row["id"])
                    )
                    atualizados += 1
                    detalhes.append(f"#{row['id']}: '{descricao_atual}' -> '{nova_descricao}' | {categoria_atual} -> {nova_categoria}")

            self.conn.commit()

            if atualizados == 0:
                return CoreResponse("Nenhum lançamento precisou de correção.")

            txt = f"🛠️ {atualizados} lançamento(s) corrigido(s):\n"
            for item in detalhes[:10]:
                txt += f"• {item}\n"
            if len(detalhes) > 10:
                txt += f"... e mais {len(detalhes) - 10} correção(ões)."
            return CoreResponse(txt)
        except Exception as e:
            return CoreResponse(f"Erro ao corrigir lançamentos: {e}")

    def listar_ultimos_lancamentos(self):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT id, data, hora, descricao, valor, tipo, categoria
                FROM lancamentos
                ORDER BY id DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

            if not rows:
                return CoreResponse("O banco está vazio. Nenhum lançamento encontrado.")

            texto = "📁 Últimos lançamentos:\n"
            for row in rows:
                texto += (
                    f"#{row['id']} | {row['data']} {row['hora']} | {row['descricao']} | "
                    f"R$ {row['valor']:.2f} | {row['tipo']} | {row['categoria']}\n"
                )

            return CoreResponse(texto)
        except Exception as e:
            return CoreResponse(f"Erro ao listar lançamentos: {e}")

    # =========================================================
    # relatórios/exportação/email
    # =========================================================
    def build_report_data(self, context=None):
        if context is None:
            context = self.last_query_context

        if not context:
            return None, "Nenhuma consulta anterior encontrada para exportar."

        rows = self.fetch_query_rows(
            context["start_date"], context["end_date"],
            context.get("categoria"), context.get("tipo"), context.get("termo_descricao")
        )

        total_pago = sum(r["valor"] for r in rows if r["tipo"] == "pago")
        total_recebido = sum(r["valor"] for r in rows if r["tipo"] == "recebido")

        por_categoria = {}
        for r in rows:
            por_categoria.setdefault(r["categoria"], {"pago": 0.0, "recebido": 0.0})
            por_categoria[r["categoria"]][r["tipo"]] += r["valor"]

        data = {
            "titulo": f"Relatório - {context['periodo_label']}",
            "periodo_label": context["periodo_label"],
            "start_date": context["start_date"],
            "end_date": context["end_date"],
            "categoria": context.get("categoria"),
            "tipo": context.get("tipo"),
            "termo_descricao": context.get("termo_descricao"),
            "total_pago": total_pago,
            "total_recebido": total_recebido,
            "saldo": total_recebido - total_pago,
            "por_categoria": por_categoria,
            "rows": rows,
        }
        return data, None

    def save_report_xml(self, report_data, filename_prefix="relatorio"):
        filepath = self.export_dir / f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

        root = Element("relatorio")
        meta = SubElement(root, "metadados")
        SubElement(meta, "titulo").text = report_data["titulo"]
        SubElement(meta, "periodo_label").text = report_data["periodo_label"]
        SubElement(meta, "data_inicio").text = report_data["start_date"].isoformat()
        SubElement(meta, "data_fim").text = report_data["end_date"].isoformat()
        SubElement(meta, "total_pago").text = f"{report_data['total_pago']:.2f}"
        SubElement(meta, "total_recebido").text = f"{report_data['total_recebido']:.2f}"
        SubElement(meta, "saldo").text = f"{report_data['saldo']:.2f}"

        categorias_el = SubElement(root, "categorias")
        for cat, vals in report_data["por_categoria"].items():
            item = SubElement(categorias_el, "categoria", nome=cat)
            SubElement(item, "pago").text = f"{vals['pago']:.2f}"
            SubElement(item, "recebido").text = f"{vals['recebido']:.2f}"

        lancs = SubElement(root, "lancamentos")
        for row in report_data["rows"]:
            item = SubElement(lancs, "lancamento", id=str(row["id"]))
            SubElement(item, "data").text = row["data"]
            SubElement(item, "hora").text = row["hora"]
            SubElement(item, "descricao").text = row["descricao"]
            SubElement(item, "valor").text = f"{row['valor']:.2f}"
            SubElement(item, "tipo").text = row["tipo"]
            SubElement(item, "categoria").text = row["categoria"]

        tree = ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
        return filepath

    def save_report_pdf(self, report_data, filename_prefix="relatorio"):
        if not REPORTLAB_OK:
            raise RuntimeError("reportlab não instalado.")

        filepath = self.export_dir / f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(str(filepath), pagesize=A4)
        width, height = A4
        y = height - 40

        def draw_line(text, step=16, font="Helvetica", size=10):
            nonlocal y
            if y < 50:
                c.showPage()
                y = height - 40
            c.setFont(font, size)
            c.drawString(40, y, str(text)[:110])
            y -= step

        draw_line(report_data["titulo"], 20, "Helvetica-Bold", 14)
        draw_line(f"Período: {self.format_date_br(report_data['start_date'])} a {self.format_date_br(report_data['end_date'])}")
        draw_line(f"Total pago: R$ {report_data['total_pago']:.2f}")
        draw_line(f"Total recebido: R$ {report_data['total_recebido']:.2f}")
        draw_line(f"Saldo: R$ {report_data['saldo']:.2f}")
        draw_line(" ")

        draw_line("Resumo por categoria:", 18, "Helvetica-Bold", 11)
        for cat, vals in report_data["por_categoria"].items():
            draw_line(f"- {cat}: pago R$ {vals['pago']:.2f} | recebido R$ {vals['recebido']:.2f}")

        draw_line(" ")
        draw_line("Lançamentos:", 18, "Helvetica-Bold", 11)
        for row in report_data["rows"]:
            draw_line(
                f"#{row['id']} | {row['data']} | {row['descricao']} | "
                f"R$ {row['valor']:.2f} | {row['tipo']} | {row['categoria']}"
            )

        c.save()
        return filepath

    def export_last_context(self, filetype="pdf", kind="resumo"):
        report_data, error = self.build_report_data()
        if error:
            return CoreResponse(error)

        prefix = "resumo" if kind == "resumo" else "relatorio"
        try:
            if filetype == "xml":
                path = self.save_report_xml(report_data, prefix)
            else:
                path = self.save_report_pdf(report_data, prefix)

            if kind == "resumo":
                txt = f"✅ Resumo em {filetype.upper()} gerado."
            else:
                txt = f"✅ Relatório em {filetype.upper()} gerado."

            return CoreResponse(txt, [path])
        except Exception as e:
            return CoreResponse(f"Erro ao exportar arquivo: {e}")

    def send_email_with_attachment(self, to_email, subject, body, attachment_path):
        host = os.getenv("SMTP_HOST")
        port = os.getenv("SMTP_PORT")
        user = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASS")
        from_email = os.getenv("SMTP_FROM", user)

        if not all([host, port, user, password, from_email]):
            raise RuntimeError("Configuração SMTP incompleta.")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body)

        with open(attachment_path, "rb") as f:
            data = f.read()

        subtype = "pdf" if attachment_path.suffix.lower() == ".pdf" else "xml"
        msg.add_attachment(data, maintype="application", subtype=subtype, filename=attachment_path.name)

        with smtplib.SMTP(host, int(port)) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

    def try_export_or_email_command(self, message):
        msg_norm = self.normalize_text(message)

        m_export = re.match(r"^exportar\s+(resumo|relatorio|relatório)\s+(pdf|xml)$", msg_norm)
        if m_export:
            kind = "resumo" if "resumo" in m_export.group(1) else "relatorio"
            filetype = m_export.group(2)
            return self.export_last_context(filetype=filetype, kind=kind)

        m_send = re.match(
            r"^enviar\s+(resumo|relatorio|relatório)\s+(pdf|xml)\s+para\s+([^\s]+@[^\s]+)$",
            msg_norm
        )
        if m_send:
            kind = "resumo" if "resumo" in m_send.group(1) else "relatorio"
            filetype = m_send.group(2)
            to_email = m_send.group(3)

            exported = self.export_last_context(filetype=filetype, kind=kind)
            if not exported.file_paths:
                return exported

            try:
                path = exported.file_paths[0]
                subject = f"{kind.capitalize()} financeiro"
                body = "Segue em anexo o arquivo solicitado."
                self.send_email_with_attachment(to_email, subject, body, path)
                return CoreResponse(f"✅ Email enviado para {to_email}.")
            except Exception as e:
                return CoreResponse(f"Erro ao enviar email: {e}")

        return None

    def try_report_command(self, message):
        msg_norm = self.normalize_text(message)

        if not re.search(r"\b(relatorio|relatório)\b", msg_norm):
            return None

        stripped = re.sub(r"\brelatorio\b|\brelatório\b", "", msg_norm).strip()
        if not stripped:
            stripped = "este mes"

        periodo_info = self.extract_query_period(stripped)
        categoria = self.detect_query_category(stripped)
        tipo = self.detect_query_type(stripped)
        termo_descricao = self.detect_query_description_term(stripped, "summary")

        context = {
            "mode": "summary",
            "start_date": periodo_info["start_date"],
            "end_date": periodo_info["end_date"],
            "categoria": categoria,
            "tipo": tipo,
            "periodo_label": periodo_info["label"],
            "termo_descricao": termo_descricao,
            "source_message": message,
            "kind": "relatorio",
        }
        self.last_query_context = context

        report_data, error = self.build_report_data(context)
        if error:
            return CoreResponse(error)

        txt = f"📑 Relatório {report_data['periodo_label']}:\n"
        if self.show_period_debug:
            txt += f"{self.period_debug_text(report_data['start_date'], report_data['end_date'])}\n"
        txt += f"Total de lançamentos: {len(report_data['rows'])}\n"
        txt += f"Total pago: R$ {report_data['total_pago']:.2f}\n"
        txt += f"Total recebido: R$ {report_data['total_recebido']:.2f}\n"
        txt += f"Saldo: R$ {report_data['saldo']:.2f}\n\n"
        txt += "Resumo por categoria:\n"

        for cat, vals in report_data["por_categoria"].items():
            txt += f"• {cat}: pago R$ {vals['pago']:.2f} | recebido R$ {vals['recebido']:.2f}\n"

        if report_data["rows"]:
            txt += "\nAmostra de lançamentos:\n"
            for row in report_data["rows"][:10]:
                txt += (
                    f"#{row['id']} | {row['data']} | {row['descricao']} | "
                    f"R$ {row['valor']:.2f} | {row['tipo']} | {row['categoria']}\n"
                )

        txt += "\nUse 'exportar relatorio pdf' ou 'exportar relatorio xml' para salvar."
        return CoreResponse(txt)

    # =========================================================
    # processador principal
    # =========================================================
    def process_message(self, message: str) -> CoreResponse:
        message_norm = self.normalize_text(message)

        if message_norm == "ajuda":
            return self.show_help()

        m_help = re.match(r"^ajuda\s+(.+)$", message_norm)
        if m_help:
            return self.show_help(m_help.group(1))

        m_search_help = re.match(r"^(buscar ajuda|pesquisar ajuda)\s+(.+)$", message_norm)
        if m_search_help:
            return self.search_help(m_search_help.group(2))

        if message_norm == "listar categorias":
            return self.list_categories()

        m_create_cat = re.match(r"^criar categoria\s+(.+?)(?:\s+com palavras\s+(.+))?$", message, re.IGNORECASE)
        if m_create_cat:
            nome = m_create_cat.group(1).strip()
            palavras = m_create_cat.group(2).strip() if m_create_cat.group(2) else ""
            return self.create_category(nome, palavras)

        patterns = [
            (r"^editar lancamento (\d+) valor ([\d.,]+)$", self.edit_launch_value),
            (r"^editar lancamento (\d+) descricao (.+)$", self.edit_launch_description),
            (r"^editar lancamento (\d+) categoria (.+)$", self.edit_launch_category),
            (r"^editar lancamento (\d+) tipo (pago|recebido)$", self.edit_launch_type),
            (r"^editar lancamento (\d+) data (\d{4}-\d{2}-\d{2})$", self.edit_launch_date),
        ]
        for pattern, handler in patterns:
            m = re.match(pattern, message, re.IGNORECASE)
            if m:
                return handler(*m.groups())

        export_response = self.try_export_or_email_command(message)
        if export_response is not None:
            return export_response

        if message_norm == "listar ultimos":
            return self.listar_ultimos_lancamentos()

        if message_norm == "corrigir lancamentos":
            return self.run_manual_fix_dirty_records()

        if message_norm in {"debug periodo on", "debug período on"}:
            self.show_period_debug = True
            return CoreResponse("Debug de período ativado.")

        if message_norm in {"debug periodo off", "debug período off"}:
            self.show_period_debug = False
            return CoreResponse("Debug de período desativado.")

        report_response = self.try_report_command(message)
        if report_response is not None:
            return report_response

        if self.looks_like_transaction(message):
            lancamento = self.extract_lancamento(message)
            if lancamento:
                ok, erro = self.save_lancamento(lancamento)
                if ok:
                    return CoreResponse(
                        f"✅ Lançamento salvo: {lancamento['descricao']} - "
                        f"R$ {lancamento['valor']:.2f} ({lancamento['tipo']}) - "
                        f"Categoria: {lancamento['categoria']} - Data: {lancamento['data']}"
                    )
                return CoreResponse(f"Falha ao salvar no banco: {erro}")

        if self.is_query(message_norm):
            query_mode = self.detect_query_mode(message_norm)
            periodo_info = self.extract_query_period(message_norm)
            categoria = self.detect_query_category(message_norm)
            tipo = self.detect_query_type(message_norm)
            termo_descricao = self.detect_query_description_term(message_norm, query_mode)

            self.last_query_context = {
                "mode": query_mode,
                "start_date": periodo_info["start_date"],
                "end_date": periodo_info["end_date"],
                "categoria": categoria,
                "tipo": tipo,
                "periodo_label": periodo_info["label"],
                "termo_descricao": termo_descricao,
                "source_message": message,
                "kind": "summary" if query_mode == "summary" else "list",
            }

            if query_mode == "list":
                return self.execute_list_query(
                    periodo_info["start_date"], periodo_info["end_date"],
                    categoria, tipo, periodo_info["label"], termo_descricao
                )

            return self.execute_summary_query(
                periodo_info["start_date"], periodo_info["end_date"],
                categoria, tipo, periodo_info["label"], termo_descricao
            )

        return CoreResponse("Não foi possível interpretar a mensagem. Digite 'ajuda' para ver os comandos.")

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass