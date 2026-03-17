import sqlite3
import re
import unicodedata
from pathlib import Path
from datetime import datetime, date, timedelta
import calendar
import speech_recognition as sr
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread, Lock
from dateutil.relativedelta import relativedelta
import pyttsx3


class WhatsAppFinanceiro:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Financeiro")
        self.root.geometry("420x760")
        self.root.configure(bg="#d9d4cf")
        self.root.resizable(False, False)

        self.base_dir = Path(__file__).resolve().parent
        self.db_path = self.base_dir / "financeiro.db"
        self.db_lock = Lock()

        self.init_database()

        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
            self.microphone_available = True
        except Exception:
            self.microphone = None
            self.microphone_available = False

        try:
            self.engine = pyttsx3.init()
            self.tts_available = True
        except Exception:
            self.engine = None
            self.tts_available = False

        self.placeholder_text = "Mensagem"
        self.show_period_debug = True

        self.categorias = {
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
            "médico": "Saúde"
        }

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

        self.setup_ui()
        self.auto_fix_dirty_records_on_startup()

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

    def init_database(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute("""
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos(data)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_categoria ON lancamentos(categoria)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_tipo ON lancamentos(tipo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_descricao ON lancamentos(descricao)")
            self.conn.commit()

    def setup_ui(self):
        self.main_container = tk.Frame(self.root, bg="#d9d4cf")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(self.main_container, bg="#0b6b63", height=72)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        back_label = tk.Label(
            header, text="←", bg="#0b6b63", fg="white", font=("Arial", 18, "bold")
        )
        back_label.pack(side=tk.LEFT, padx=(10, 6), pady=10)

        avatar = tk.Canvas(header, width=38, height=38, bg="#0b6b63", highlightthickness=0)
        avatar.pack(side=tk.LEFT, pady=10)
        avatar.create_oval(2, 2, 36, 36, fill="#6d98c9", outline="white", width=2)
        avatar.create_text(19, 19, text="💰", font=("Arial", 14))

        title_frame = tk.Frame(header, bg="#0b6b63")
        title_frame.pack(side=tk.LEFT, padx=8, pady=10)

        tk.Label(
            title_frame,
            text="WhatsApp Financeiro",
            bg="#0b6b63",
            fg="white",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="Online",
            bg="#0b6b63",
            fg="white",
            font=("Arial", 8)
        ).pack(anchor="w")

        icons_frame = tk.Frame(header, bg="#0b6b63")
        icons_frame.pack(side=tk.RIGHT, padx=8)

        tk.Label(icons_frame, text="📞", bg="#0b6b63", fg="white", font=("Arial", 14)).pack(side=tk.LEFT, padx=4)
        tk.Label(icons_frame, text="⋮", bg="#0b6b63", fg="white", font=("Arial", 16)).pack(side=tk.LEFT, padx=4)

        chat_wrapper = tk.Frame(self.main_container, bg="#d9d4cf")
        chat_wrapper.pack(fill=tk.BOTH, expand=True)

        self.chat_area = scrolledtext.ScrolledText(
            chat_wrapper,
            wrap=tk.WORD,
            font=("Arial", 9),
            bg="#e5ddd5",
            fg="#111111",
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=10
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)

        self.chat_area.tag_config("usuario_nome", foreground="#075e54", font=("Arial", 9, "bold"))
        self.chat_area.tag_config("sistema_nome", foreground="#128c7e", font=("Arial", 9, "bold"))
        self.chat_area.tag_config("erro_nome", foreground="#b00020", font=("Arial", 9, "bold"))
        self.chat_area.tag_config("texto_usuario", foreground="#111111", font=("Arial", 9))
        self.chat_area.tag_config("texto_sistema", foreground="#111111", font=("Arial", 9))
        self.chat_area.tag_config("texto_erro", foreground="#b00020", font=("Arial", 9))

        bottom_frame = tk.Frame(self.main_container, bg="#d9d4cf", height=72)
        bottom_frame.pack(fill=tk.X, padx=8, pady=6)
        bottom_frame.pack_propagate(False)

        input_box = tk.Frame(bottom_frame, bg="white", height=46)
        input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)
        input_box.pack_propagate(False)

        emoji_btn = tk.Button(
            input_box, text="☺", command=lambda: None,
            bg="white", fg="#888888", relief=tk.FLAT, font=("Arial", 14)
        )
        emoji_btn.pack(side=tk.LEFT, padx=(6, 2))

        self.message_entry = tk.Entry(
            input_box, font=("Arial", 11), relief=tk.FLAT, bd=0, fg="#888888"
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=10)
        self.message_entry.bind("<Return>", lambda e: self.send_text_message())
        self.message_entry.bind("<FocusIn>", self.clear_placeholder)
        self.message_entry.bind("<FocusOut>", self.restore_placeholder)

        self.set_placeholder()

        attach_btn = tk.Button(
            input_box, text="📎", command=self.force_extract,
            bg="white", fg="#777777", relief=tk.FLAT, font=("Arial", 12)
        )
        attach_btn.pack(side=tk.LEFT, padx=2)

        query_btn = tk.Button(
            input_box, text="📊", command=self.show_query_dialog,
            bg="white", fg="#777777", relief=tk.FLAT, font=("Arial", 12)
        )
        query_btn.pack(side=tk.LEFT, padx=(2, 6))

        self.audio_btn = tk.Button(
            bottom_frame,
            text="🎤",
            command=self.start_audio_recognition,
            bg="#00a884",
            fg="white",
            relief=tk.FLAT,
            font=("Arial", 14, "bold"),
            width=3,
            height=1,
            activebackground="#00a884",
            activeforeground="white"
        )
        self.audio_btn.pack(side=tk.RIGHT, padx=(6, 0), pady=6)

        self.add_message("sistema", "💰 WhatsApp Financeiro iniciado.")
        self.add_message(
            "sistema",
            "Ações rápidas: lançar | listar | resumo | ajuda\n"
            "Exemplos: 'Paguei 35 de gasolina dia 23/02' | 'Resumo março'"
        )

        if not self.microphone_available:
            self.add_message("erro", "Microfone não disponível nesta máquina.")

        if not self.tts_available:
            self.add_message("erro", "Sintetizador de voz não disponível nesta máquina.")

    def set_placeholder(self):
        self.message_entry.delete(0, tk.END)
        self.message_entry.insert(0, self.placeholder_text)
        self.message_entry.config(fg="#888888")

    def clear_placeholder(self, event=None):
        if self.message_entry.get() == self.placeholder_text:
            self.message_entry.delete(0, tk.END)
            self.message_entry.config(fg="#111111")

    def restore_placeholder(self, event=None):
        if not self.message_entry.get().strip():
            self.set_placeholder()

    def get_entry_text(self):
        text = self.message_entry.get().strip()
        if text == self.placeholder_text:
            return ""
        return text

    def clear_entry_after_send(self):
        self.message_entry.delete(0, tk.END)
        self.message_entry.config(fg="#111111")

    def add_message(self, sender, message):
        timestamp = datetime.now().strftime("%H:%M")

        if sender == "usuario":
            self.chat_area.insert(tk.END, f"Você  {timestamp}\n", "usuario_nome")
            self.chat_area.insert(tk.END, f"{message}\n\n", "texto_usuario")
        elif sender == "sistema":
            self.chat_area.insert(tk.END, f"Sistema  {timestamp}\n", "sistema_nome")
            self.chat_area.insert(tk.END, f"{message}\n\n", "texto_sistema")
        elif sender == "erro":
            self.chat_area.insert(tk.END, f"Erro  {timestamp}\n", "erro_nome")
            self.chat_area.insert(tk.END, f"{message}\n\n", "texto_erro")

        self.chat_area.see(tk.END)

    def send_text_message(self):
        message = self.get_entry_text()
        if message:
            self.add_message("usuario", message)
            self.clear_entry_after_send()
            self.process_message(message)

    def force_extract(self):
        message = self.get_entry_text()
        if message:
            self.send_text_message()

    def start_audio_recognition(self):
        if not self.microphone_available:
            self.add_message("erro", "Microfone não disponível.")
            return

        self.audio_btn.config(state=tk.DISABLED, text="...")
        Thread(target=self.recognize_audio, daemon=True).start()

    def recognize_audio(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)

            text = self.recognizer.recognize_google(audio, language="pt-BR")
            self.root.after(0, lambda: self.audio_recognition_callback(text))

        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.audio_recognition_callback(None, "Tempo de áudio esgotado"))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.audio_recognition_callback(None, "Não foi possível entender o áudio"))
        except Exception as e:
            self.root.after(0, lambda: self.audio_recognition_callback(None, f"Erro: {str(e)}"))

    def audio_recognition_callback(self, text, error=None):
        self.audio_btn.config(state=tk.NORMAL, text="🎤")

        if error:
            self.add_message("erro", error)
        elif text:
            self.add_message("usuario", f"🎤 {text}")
            self.process_message(text)

    def show_help(self):
        help_text = (
            "📘 AJUDA\n"
            "────────────────\n"
            "LANÇAMENTOS\n"
            "• Paguei 35 de gasolina hoje\n"
            "• Gastei 80 em mercado dia 05/03\n"
            "• Recebi 1200 de salário\n"
            "• Recebi 2500 de aposentadoria\n"
            "• Recebi 900 de aluguel\n\n"
            "CONSULTAS DE RESUMO\n"
            "• Resumo este mês\n"
            "• Resumo março\n"
            "• Quanto gastei em fevereiro\n"
            "• Quanto gastei de combustível mês passado\n"
            "• Resumo primeira semana de janeiro\n"
            "• Resumo de 23/02 a 06/03\n"
            "• Resumo entre 23 de fevereiro e 6 de março\n"
            "• Resumo últimos 7 dias\n"
            "• Resumo última semana\n"
            "• Resumo semana passada\n"
            "• Resumo últimos 45 dias\n"
            "• Resumo últimos 8 meses\n"
            "• Resumo do ano\n"
            "• Resumo de ano 2025\n"
            "• Resumo do dia 10/01 até 18/02\n"
            "• Resumo de janeiro até março\n\n"
            "LISTAGENS\n"
            "• Listar março\n"
            "• Listar transferencias\n"
            "• Listar recebidos março\n"
            "• Listar pagos fevereiro\n"
            "• Listar outros\n"
            "• Listar combustivel\n"
            "• Listar de 23 de fevereiro a 6 de março\n"
            "• Listar últimos 15 dias\n"
            "• Listar ano 2024\n\n"
            "REGRAS DE SEMANA\n"
            "• semana passada = semana calendário anterior (segunda a domingo)\n"
            "• última semana = últimos 7 dias reais\n\n"
            "UTILITÁRIOS\n"
            "• listar ultimos\n"
            "• corrigir lancamentos\n"
            "• ajuda"
        )
        self.add_message("sistema", help_text)

    def process_message(self, message):
        message_norm = self.normalize_text(message)

        if message_norm == "ajuda":
            self.show_help()
            return

        if message_norm == "listar ultimos":
            self.listar_ultimos_lancamentos()
            return

        if message_norm == "corrigir lancamentos":
            self.run_manual_fix_dirty_records()
            return

        if self.looks_like_transaction(message):
            lancamento = self.extract_lancamento(message)
            if lancamento:
                ok, erro = self.save_lancamento(lancamento)
                if ok:
                    self.add_message(
                        "sistema",
                        f"✅ Lançamento salvo: {lancamento['descricao']} - "
                        f"R$ {lancamento['valor']:.2f} ({lancamento['tipo']}) - "
                        f"Categoria: {lancamento['categoria']} - Data: {lancamento['data']}"
                    )
                    self.speak(
                        f"Lançamento de {lancamento['tipo']} no valor de "
                        f"{lancamento['valor']:.2f} reais salvo com sucesso"
                    )
                else:
                    self.add_message("erro", f"Falha ao salvar no banco: {erro}")
                return

        if self.is_query(message_norm):
            self.process_query(message)
            return

        self.add_message(
            "erro",
            "Não foi possível interpretar a mensagem. Digite 'ajuda' para ver os comandos disponíveis."
        )

    def looks_like_transaction(self, message):
        message_norm = self.normalize_text(message)

        transaction_verbs = [
            "paguei", "gastei", "comprei", "recebi", "ganhei",
            "depositaram", "entrou", "debitei"
        ]

        has_transaction_verb = any(re.search(rf"\b{verb}\b", message_norm) for verb in transaction_verbs)
        has_value = self.extract_value(message) is not None

        return has_transaction_verb and has_value

    def is_query(self, message_norm):
        query_patterns = [
            r"\bquanto\b",
            r"\bqual\b",
            r"\bresumo\b",
            r"\bextrato\b",
            r"\bsaldo\b",
            r"\btotal\b",
            r"\bmostre\b",
            r"\bliste\b",
            r"\blistar\b",
            r"\bquais\b",
            r"\bentre\b",
            r"\bprimeira semana\b",
            r"\bsegunda semana\b",
            r"\bterceira semana\b",
            r"\bquarta semana\b",
            r"\bquinta semana\b",
            r"\bultima semana\b",
            r"\búltima semana\b",
            r"\bsemana passada\b",
            r"\bultimos \d+ dias\b",
            r"\búltimos \d+ dias\b",
            r"\bultimos \d+ meses\b",
            r"\búltimos \d+ meses\b",
            r"\bdo ano\b",
            r"\bano \d{4}\b",
            r"\bde .* ate .*\b",
            r"\bde .* até .*\b",
            r"\bdo dia .* ate .*\b",
            r"\bdo dia .* até .*\b",
        ]

        if any(re.search(pattern, message_norm) for pattern in query_patterns):
            return True

        if re.search(r"\b(gastos|despesas|receitas|recebimentos)\b", message_norm):
            return True

        if re.search(r"\bmes passado\b", message_norm):
            return True

        if re.search(r"\b(esse mes|este mes|hoje|ontem)\b", message_norm):
            return True

        if re.search(r"\bde\s+\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\s+a\s+\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", message_norm):
            return True

        if re.search(r"\b(?:dia\s+)?\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", message_norm) and not self.looks_like_transaction(message_norm):
            return True

        for mes in self.meses.keys():
            if re.search(rf"\b{self.normalize_text(mes)}\b", message_norm) and not self.looks_like_transaction(message_norm):
                return True

        for palavra in [
            "transferencias", "transferencia", "pix", "outros", "saude", "mercado",
            "combustivel", "contas", "renda", "alimentacao", "transporte",
            "recebidos", "pagos", "aposentadoria", "aluguel"
        ]:
            if re.search(rf"\b{palavra}\b", message_norm) and not self.looks_like_transaction(message_norm):
                return True

        return False

    def process_query(self, message):
        message_norm = self.normalize_text(message)

        query_mode = self.detect_query_mode(message_norm)
        periodo_info = self.extract_query_period(message_norm)
        categoria = self.detect_query_category(message_norm)
        tipo = self.detect_query_type(message_norm)
        termo_descricao = self.detect_query_description_term(message_norm, query_mode)

        if query_mode == "list":
            self.execute_list_query(
                start_date=periodo_info["start_date"],
                end_date=periodo_info["end_date"],
                categoria=categoria,
                tipo=tipo,
                periodo_label=periodo_info["label"],
                termo_descricao=termo_descricao
            )
        else:
            self.execute_summary_query(
                start_date=periodo_info["start_date"],
                end_date=periodo_info["end_date"],
                categoria=categoria,
                tipo=tipo,
                periodo_label=periodo_info["label"],
                termo_descricao=termo_descricao
            )

    def detect_query_mode(self, message_norm):
        if re.search(r"\b(listar|liste|mostre|quais)\b", message_norm):
            return "list"
        return "summary"

    def parse_date_token(self, day_str, month_str, year_str=None, default_year=None):
        if default_year is None:
            default_year = date.today().year

        try:
            day = int(day_str)
            if month_str.isdigit():
                month = int(month_str)
            else:
                month = self.meses.get(self.normalize_text(month_str))

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
            return {
                "start_date": start_date,
                "end_date": end_date,
                "label": "última semana"
            }

        match = re.search(r"\b(?:ultimos|últimos)\s+(\d{1,3})\s+dias\b", message_norm)
        if not match:
            return None

        qtd = int(match.group(1))
        if qtd < 1 or qtd > 365:
            return None

        end_date = date.today()
        start_date = end_date - timedelta(days=qtd - 1)

        label = f"últimos {qtd} dias"
        return {"start_date": start_date, "end_date": end_date, "label": label}

    def extract_relative_months_period(self, message_norm):
        match = re.search(r"\b(?:ultimos|últimos)\s+(\d{1,2})\s+meses\b", message_norm)
        if not match:
            return None

        qtd = int(match.group(1))
        if qtd < 1 or qtd > 12:
            return None

        end_date = date.today()
        start_date = end_date - relativedelta(months=qtd) + timedelta(days=1)

        label = f"últimos {qtd} meses"
        return {"start_date": start_date, "end_date": end_date, "label": label}

    def extract_last_week_period(self, message_norm):
        if "semana passada" not in message_norm:
            return None

        today = date.today()
        start_of_current_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_current_week - timedelta(days=7)
        end_of_last_week = start_of_current_week - timedelta(days=1)

        return {
            "start_date": start_of_last_week,
            "end_date": end_of_last_week,
            "label": "semana passada"
        }

    def extract_year_period(self, message_norm):
        today = date.today()

        if re.search(r"\bdo ano\b", message_norm):
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
            return {
                "start_date": start_date,
                "end_date": end_date,
                "label": f"ano de {today.year}"
            }

        match = re.search(r"\bano\s+(\d{4})\b", message_norm)
        if match:
            ano = int(match.group(1))
            start_date = date(ano, 1, 1)
            end_date = date(ano, 12, 31)
            return {
                "start_date": start_date,
                "end_date": end_date,
                "label": f"ano de {ano}"
            }

        return None

    def extract_week_period(self, message_norm):
        pattern = (
            r"\b(primeira|segunda|terceira|quarta|quinta|ultima|última)\s+semana\s+de\s+"
            r"(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"(?:\s+de\s+(\d{4}))?\b"
        )
        match = re.search(pattern, message_norm)
        if not match:
            return None

        ordinal_txt, mes_txt, ano_txt = match.groups()
        mes_num = self.meses[self.normalize_text(mes_txt)]
        ano = int(ano_txt) if ano_txt else date.today().year

        ultimo_dia_mes = calendar.monthrange(ano, mes_num)[1]
        ultimo_dia = date(ano, mes_num, ultimo_dia_mes)

        ordinal = self.ordinais_semana[self.normalize_text(ordinal_txt)]

        if ordinal == 99:
            start_day = max(1, ultimo_dia_mes - 6)
            start_date = date(ano, mes_num, start_day)
            end_date = ultimo_dia
            label = f"última semana de {self.meses_exibicao[mes_num]} de {ano}"
            return {"start_date": start_date, "end_date": end_date, "label": label}

        start_day = 1 + (ordinal - 1) * 7
        if start_day > ultimo_dia_mes:
            return None

        end_day = min(start_day + 6, ultimo_dia_mes)
        start_date = date(ano, mes_num, start_day)
        end_date = date(ano, mes_num, end_day)

        label = f"{ordinal_txt} semana de {self.meses_exibicao[mes_num]} de {ano}"
        return {"start_date": start_date, "end_date": end_date, "label": label}

    def extract_range_period(self, message_norm):
        current_year = date.today().year

        pattern_numeric = (
            r"\b(?:de|entre|do dia)\s+(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?"
            r"\s+(?:a|ate|até|e)\s+"
            r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b"
        )
        match = re.search(pattern_numeric, message_norm)
        if match:
            d1, m1, y1, d2, m2, y2 = match.groups()
            start_date = self.parse_date_token(d1, m1, y1, current_year)
            end_date = self.parse_date_token(d2, m2, y2, current_year)
            if start_date and end_date:
                if end_date < start_date:
                    start_date, end_date = end_date, start_date
                label = f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
                return {"start_date": start_date, "end_date": end_date, "label": label}

        pattern_textual = (
            r"\b(?:de|entre|do dia)\s+(\d{1,2})\s+de\s+"
            r"(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"(?:\s+de\s+(\d{4}))?"
            r"\s+(?:a|ate|até|e)\s+"
            r"(\d{1,2})\s+de\s+"
            r"(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"(?:\s+de\s+(\d{4}))?\b"
        )
        match = re.search(pattern_textual, message_norm)
        if match:
            d1, m1, y1, d2, m2, y2 = match.groups()
            start_date = self.parse_date_token(d1, m1, y1, current_year)
            end_date = self.parse_date_token(d2, m2, y2, current_year)
            if start_date and end_date:
                if end_date < start_date:
                    start_date, end_date = end_date, start_date
                label = f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
                return {"start_date": start_date, "end_date": end_date, "label": label}

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
        match = re.search(pattern, message_norm)
        if not match:
            return None

        mes1_txt, ano1_txt, mes2_txt, ano2_txt = match.groups()

        ano_atual = date.today().year
        mes1 = self.meses[self.normalize_text(mes1_txt)]
        mes2 = self.meses[self.normalize_text(mes2_txt)]
        ano1 = int(ano1_txt) if ano1_txt else ano_atual
        ano2 = int(ano2_txt) if ano2_txt else ano1

        start_date = date(ano1, mes1, 1)
        end_day = calendar.monthrange(ano2, mes2)[1]
        end_date = date(ano2, mes2, end_day)

        if end_date < start_date:
            start_date, end_date = end_date, start_date

        label = (
            f"{self.meses_exibicao[start_date.month]} de {start_date.year} "
            f"até {self.meses_exibicao[end_date.month]} de {end_date.year}"
        )
        return {"start_date": start_date, "end_date": end_date, "label": label}

    def extract_query_period(self, message_norm):
        today = date.today()

        relative_days = self.extract_relative_days_period(message_norm)
        if relative_days:
            return relative_days

        relative_months = self.extract_relative_months_period(message_norm)
        if relative_months:
            return relative_months

        last_week = self.extract_last_week_period(message_norm)
        if last_week:
            return last_week

        year_period = self.extract_year_period(message_norm)
        if year_period:
            return year_period

        range_period = self.extract_range_period(message_norm)
        if range_period:
            return range_period

        month_range_period = self.extract_month_range_period(message_norm)
        if month_range_period:
            return month_range_period

        week_period = self.extract_week_period(message_norm)
        if week_period:
            return week_period

        date_specific = self.extract_specific_date_from_text(message_norm)
        if date_specific:
            return {
                "start_date": date_specific,
                "end_date": date_specific,
                "label": date_specific.strftime("%d/%m/%Y")
            }

        for mes_nome, mes_num in self.meses.items():
            mes_norm = self.normalize_text(mes_nome)
            if re.search(rf"\b{mes_norm}\b", message_norm):
                ano = today.year
                ano_match = re.search(rf"\b{mes_norm}\s+de\s+(\d{{4}})\b", message_norm)
                if ano_match:
                    ano = int(ano_match.group(1))

                start_date = date(ano, mes_num, 1)
                ultimo_dia = calendar.monthrange(ano, mes_num)[1]
                end_date = date(ano, mes_num, ultimo_dia)

                return {
                    "start_date": start_date,
                    "end_date": end_date,
                    "label": f"{self.meses_exibicao[mes_num]} de {ano}"
                }

        if "mes passado" in message_norm:
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - relativedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return {
                "start_date": first_day_last_month,
                "end_date": last_day_last_month,
                "label": "mês passado"
            }

        if "esse mes" in message_norm or "este mes" in message_norm or re.search(r"\bresumo mes\b", message_norm):
            return {
                "start_date": today.replace(day=1),
                "end_date": today,
                "label": "este mês"
            }

        if "hoje" in message_norm:
            return {"start_date": today, "end_date": today, "label": "hoje"}

        if "ontem" in message_norm:
            yesterday = today - relativedelta(days=1)
            return {"start_date": yesterday, "end_date": yesterday, "label": "ontem"}

        return {
            "start_date": today.replace(day=1),
            "end_date": today,
            "label": "este mês"
        }

    def extract_specific_date_from_text(self, text):
        match = re.search(r"\b(?:dia\s+)?(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
        if not match:
            return None

        day, month, year = match.groups()
        today = date.today()

        try:
            year = int(year) if year else today.year
            if year < 100:
                year += 2000
            return date(year, int(month), int(day))
        except ValueError:
            return None

    def detect_query_category(self, message_norm):
        category_aliases = {
            "Combustível": ["combustivel", "gasolina", "etanol", "diesel", "alcool"],
            "Transferências": ["transferencias", "transferencia", "pix"],
            "Saúde": ["saude", "remedio", "remedios", "farmacia", "medico"],
            "Mercado": ["mercado", "supermercado"],
            "Contas": ["contas", "agua", "luz", "internet", "energia"],
            "Renda": ["renda", "salario", "freela", "aposentadoria", "aluguel"],
            "Alimentação": ["alimentacao", "restaurante", "lanche", "ifood", "padaria"],
            "Transporte": ["transporte", "uber", "99", "onibus"],
            "Outros": ["outros", "outro"]
        }

        for categoria, aliases in category_aliases.items():
            for alias in aliases:
                if re.search(rf"\b{alias}\b", message_norm):
                    return categoria

        for keyword, category in self.categorias.items():
            if self.normalize_text(keyword) in message_norm:
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
            "transferencias", "transferencia", "pix", "outros", "combustivel",
            "saude", "mercado", "contas", "renda", "alimentacao", "transporte",
            "primeira", "segunda", "terceira", "quarta", "quinta", "ultima", "última",
            "semana", "entre", "ate", "até", "a", "ultimos", "últimos", "dias",
            "meses", "ano", "aposentadoria", "aluguel", "do"
        }

        if query_mode == "list":
            return None

        if "gasolina" in message_norm:
            return "gasolina"
        if "remedio" in message_norm or "remedios" in message_norm:
            return "remedio"

        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", message_norm)
        candidatos = [t for t in tokens if t not in termos_ignorar]

        for token in candidatos:
            if re.fullmatch(r"\d{1,4}", token):
                continue
            return token

        return None

    def execute_summary_query(self, start_date, end_date, categoria, tipo, periodo_label, termo_descricao=None):
        try:
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

            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                resultados = cursor.fetchall()

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
                self.add_message("sistema", texto)
                return

            total_pago = sum(r["valor"] for r in resultados if r["tipo"] == "pago")
            total_recebido = sum(r["valor"] for r in resultados if r["tipo"] == "recebido")

            categorias = {}
            for r in resultados:
                cat = r["categoria"]
                if cat not in categorias:
                    categorias[cat] = {"pago": 0.0, "recebido": 0.0}
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

            self.add_message("sistema", response)
            self.speak(
                f"Resumo de {periodo_label}. Total pago: {total_pago:.2f} reais. "
                f"Total recebido: {total_recebido:.2f} reais."
            )
        except Exception as e:
            self.add_message("erro", f"Erro ao consultar banco: {e}")

    def execute_list_query(self, start_date, end_date, categoria, tipo, periodo_label, termo_descricao=None):
        try:
            query = """
                SELECT id, data, hora, descricao, valor, tipo, categoria
                FROM lancamentos
                WHERE date(data) BETWEEN ? AND ?
            """
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

            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

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
                self.add_message("sistema", texto)
                return

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

            self.add_message("sistema", texto)
        except Exception as e:
            self.add_message("erro", f"Erro ao listar lançamentos: {e}")

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

    def extract_value(self, message):
        match = re.search(r"\b(?:r\$|rs)?\s*(\d+[.,]\d+|\d+)\s*(?:reais|r\$)?\b", message, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                return None
        return None

    def determine_tipo_lancamento(self, message_norm):
        palavras_pago = ["paguei", "gastei", "comprei", "debitei", "despesa", "pago"]
        palavras_recebido = [
            "recebi", "ganhei", "entrou", "depositaram", "salario",
            "freela", "renda", "receita", "aposentadoria", "aluguel"
        ]

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

        texto = re.sub(
            r"\b(paguei|gastei|comprei|recebi|ganhei|entrou|depositaram|pagar|gastar|comprar|debitei)\b",
            " ",
            texto
        )

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

        if not texto:
            return "Lançamento"

        return texto

    def determine_category(self, message_norm):
        if any(x in message_norm for x in ["gasolina", "combustivel", "etanol", "diesel", "alcool"]):
            return "Combustível"
        if any(x in message_norm for x in ["pix", "transferencia", "transferencias"]):
            return "Transferências"
        if any(x in message_norm for x in ["aposentadoria", "aluguel", "salario", "freela", "renda"]):
            return "Renda"

        for keyword, category in self.categorias.items():
            if self.normalize_text(keyword) in message_norm:
                return category
        return "Outros"

    def extract_date_time(self, message):
        today = datetime.now()
        message_norm = self.normalize_text(message)

        if "ontem" in message_norm:
            data = (today - relativedelta(days=1)).strftime("%Y-%m-%d")
        elif "amanha" in message_norm:
            data = (today + relativedelta(days=1)).strftime("%Y-%m-%d")
        elif "hoje" in message_norm:
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

        hora = today.strftime("%H:%M:%S")
        return data, hora

    def save_lancamento(self, lancamento):
        try:
            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO lancamentos
                    (data, hora, descricao, valor, tipo, categoria, mensagem_original)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    lancamento["data"],
                    lancamento["hora"],
                    lancamento["descricao"],
                    lancamento["valor"],
                    lancamento["tipo"],
                    lancamento["categoria"],
                    lancamento["mensagem_original"]
                ))
                self.conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)

    def description_looks_dirty(self, descricao):
        desc = self.normalize_text(descricao)
        if not desc:
            return True

        dirty_patterns = [
            r"/",
            r"\b(pagueide|gasteide|gasolinadia)\b",
            r"\bdia\b",
            r"^\bde\b",
            r"\bde$",
        ]

        if len(desc) <= 2:
            return True

        for pattern in dirty_patterns:
            if re.search(pattern, desc):
                return True

        return False

    def rebuild_description_from_original(self, mensagem_original, descricao_atual):
        base_text = mensagem_original if mensagem_original else descricao_atual
        nova_descricao = self.extract_description(base_text)

        mapa_prioridade = [
            ("gasolina", "gasolina"),
            ("combustivel", "combustivel"),
            ("etanol", "etanol"),
            ("diesel", "diesel"),
            ("pix", "pix"),
            ("transferencia", "transferencia"),
            ("aposentadoria", "aposentadoria"),
            ("aluguel", "aluguel"),
            ("remedios", "remedios"),
            ("remedio", "remedio"),
            ("farmacia", "farmacia"),
            ("medico", "medico"),
            ("uber", "uber"),
            ("mercado", "mercado"),
            ("salario", "salario"),
            ("ifood", "ifood"),
            ("padaria", "padaria"),
            ("internet", "internet"),
            ("agua", "agua"),
            ("luz", "luz"),
        ]

        texto_norm = self.normalize_text(base_text)
        for termo, saida in mapa_prioridade:
            if termo in texto_norm:
                return saida

        return nova_descricao if nova_descricao else descricao_atual

    def recalculate_category_from_original(self, mensagem_original, descricao):
        base_text = f"{mensagem_original or ''} {descricao or ''}"
        return self.determine_category(self.normalize_text(base_text))

    def auto_fix_dirty_records_on_startup(self):
        try:
            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT id, descricao, categoria, mensagem_original
                    FROM lancamentos
                    ORDER BY id ASC
                """)
                rows = cursor.fetchall()

                atualizados = 0

                for row in rows:
                    descricao_atual = row["descricao"] or ""
                    mensagem_original = row["mensagem_original"] or ""
                    categoria_atual = row["categoria"] or "Outros"

                    if not self.description_looks_dirty(descricao_atual):
                        continue

                    nova_descricao = self.rebuild_description_from_original(mensagem_original, descricao_atual)
                    nova_categoria = self.recalculate_category_from_original(mensagem_original, nova_descricao)

                    if (nova_descricao != descricao_atual) or (nova_categoria != categoria_atual):
                        cursor.execute("""
                            UPDATE lancamentos
                            SET descricao = ?, categoria = ?
                            WHERE id = ?
                        """, (nova_descricao, nova_categoria, row["id"]))
                        atualizados += 1

                self.conn.commit()

            if atualizados > 0:
                self.add_message("sistema", f"🛠️ Correção automática aplicada em {atualizados} lançamento(s) antigos.")
        except Exception as e:
            self.add_message("erro", f"Erro na correção automática inicial: {e}")

    def run_manual_fix_dirty_records(self):
        try:
            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT id, descricao, categoria, mensagem_original
                    FROM lancamentos
                    ORDER BY id ASC
                """)
                rows = cursor.fetchall()

                atualizados = 0
                detalhes = []

                for row in rows:
                    descricao_atual = row["descricao"] or ""
                    mensagem_original = row["mensagem_original"] or ""
                    categoria_atual = row["categoria"] or "Outros"

                    nova_descricao = self.rebuild_description_from_original(mensagem_original, descricao_atual)
                    nova_categoria = self.recalculate_category_from_original(mensagem_original, nova_descricao)

                    if (nova_descricao != descricao_atual) or (nova_categoria != categoria_atual):
                        cursor.execute("""
                            UPDATE lancamentos
                            SET descricao = ?, categoria = ?
                            WHERE id = ?
                        """, (nova_descricao, nova_categoria, row["id"]))
                        atualizados += 1
                        detalhes.append(
                            f"#{row['id']}: '{descricao_atual}' -> '{nova_descricao}' | {categoria_atual} -> {nova_categoria}"
                        )

                self.conn.commit()

            if atualizados == 0:
                self.add_message("sistema", "Nenhum lançamento precisou de correção.")
                return

            texto = f"🛠️ {atualizados} lançamento(s) corrigido(s):\n"
            for item in detalhes[:10]:
                texto += f"• {item}\n"

            if len(detalhes) > 10:
                texto += f"... e mais {len(detalhes) - 10} correção(ões)."

            self.add_message("sistema", texto)
        except Exception as e:
            self.add_message("erro", f"Erro ao corrigir lançamentos: {e}")

    def listar_ultimos_lancamentos(self):
        try:
            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT id, data, hora, descricao, valor, tipo, categoria
                    FROM lancamentos
                    ORDER BY id DESC
                    LIMIT 10
                """)
                rows = cursor.fetchall()

            if not rows:
                self.add_message("sistema", "O banco está vazio. Nenhum lançamento encontrado.")
                return

            texto = "📁 Últimos lançamentos:\n"
            for row in rows:
                texto += (
                    f"#{row['id']} | {row['data']} {row['hora']} | "
                    f"{row['descricao']} | R$ {row['valor']:.2f} | "
                    f"{row['tipo']} | {row['categoria']}\n"
                )

            self.add_message("sistema", texto)
        except Exception as e:
            self.add_message("erro", f"Erro ao listar lançamentos: {e}")

    def show_query_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Consulta Personalizada")
        dialog.geometry("340x170")
        dialog.configure(bg="#e5ddd5")
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text="Digite sua consulta:",
            font=("Arial", 11, "bold"),
            bg="#e5ddd5",
            fg="#075e54"
        ).pack(pady=12)

        query_entry = tk.Entry(dialog, font=("Arial", 10), width=34)
        query_entry.pack(pady=5)
        query_entry.insert(0, "Ex: Quanto gastei com combustível esse mês?")

        def execute_custom_query():
            query = query_entry.get().strip()
            if query and query != "Ex: Quanto gastei com combustível esse mês?":
                self.add_message("usuario", query)
                self.process_message(query)
                dialog.destroy()

        tk.Button(
            dialog,
            text="Consultar",
            command=execute_custom_query,
            bg="#25D366",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=6
        ).pack(pady=15)

    def speak(self, text):
        if not self.tts_available or self.engine is None:
            return

        def speak_thread():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass

        Thread(target=speak_thread, daemon=True).start()

    def run(self):
        self.root.mainloop()

    def __del__(self):
        try:
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    app = WhatsAppFinanceiro()
    app.run()