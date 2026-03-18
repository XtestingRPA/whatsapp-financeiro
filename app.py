from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext
from threading import Thread

import speech_recognition as sr
import pyttsx3

from finance_core import FinanceCore, UserContext


class WhatsAppFinanceiroApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Financeiro")
        self.root.geometry("380x660")
        self.root.configure(bg="#d9d4cf")
        self.root.resizable(False, False)

        self.core = FinanceCore()
        self.user_context = UserContext(canal="local", usuario_id="desktop_user", chat_id="desktop_chat")
        self.placeholder_text = "Mensagem"

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

        self.setup_ui()

    def setup_ui(self):
        self.main_container = tk.Frame(self.root, bg="#d9d4cf")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(self.main_container, bg="#0b6b63", height=72)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="←", bg="#0b6b63", fg="white", font=("Arial", 18, "bold")).pack(side=tk.LEFT, padx=(10, 6), pady=10)

        avatar = tk.Canvas(header, width=38, height=38, bg="#0b6b63", highlightthickness=0)
        avatar.pack(side=tk.LEFT, pady=10)
        avatar.create_oval(2, 2, 36, 36, fill="#6d98c9", outline="white", width=2)
        avatar.create_text(19, 19, text="💰", font=("Arial", 14))

        title_frame = tk.Frame(header, bg="#0b6b63")
        title_frame.pack(side=tk.LEFT, padx=8, pady=10)
        tk.Label(title_frame, text="WhatsApp Financeiro", bg="#0b6b63", fg="white", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Online", bg="#0b6b63", fg="white", font=("Arial", 8)).pack(anchor="w")

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

        tk.Button(input_box, text="☺", command=lambda: None, bg="white", fg="#888888", relief=tk.FLAT, font=("Arial", 14)).pack(side=tk.LEFT, padx=(6, 2))

        self.message_entry = tk.Entry(input_box, font=("Arial", 11), relief=tk.FLAT, bd=0, fg="#888888")
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=10)
        self.message_entry.bind("<Return>", lambda e: self.send_text_message())
        self.message_entry.bind("<FocusIn>", self.clear_placeholder)
        self.message_entry.bind("<FocusOut>", self.restore_placeholder)
        self.set_placeholder()

        tk.Button(input_box, text="📎", command=self.force_extract, bg="white", fg="#777777", relief=tk.FLAT, font=("Arial", 12)).pack(side=tk.LEFT, padx=2)

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
        )
        self.audio_btn.pack(side=tk.RIGHT, padx=(6, 0), pady=6)

        self.add_message("sistema", "💰 WhatsApp Financeiro iniciado.")
        self.add_message("sistema", "Ações rápidas: lançar | listar | resumo | relatorio | ajuda")

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

    def add_message(self, sender, message):
        if sender == "usuario":
            self.chat_area.insert(tk.END, "Você\n", "usuario_nome")
            self.chat_area.insert(tk.END, f"{message}\n\n", "texto_usuario")
        elif sender == "sistema":
            self.chat_area.insert(tk.END, "Sistema\n", "sistema_nome")
            self.chat_area.insert(tk.END, f"{message}\n\n", "texto_sistema")
        else:
            self.chat_area.insert(tk.END, "Erro\n", "erro_nome")
            self.chat_area.insert(tk.END, f"{message}\n\n", "texto_erro")
        self.chat_area.see(tk.END)

    def send_text_message(self):
        message = self.message_entry.get().strip()
        if message and message != self.placeholder_text:
            self.add_message("usuario", message)
            self.message_entry.delete(0, tk.END)
            self.restore_placeholder()

            response = self.core.process_message(message, user=self.user_context)
            if response.file_paths:
                nomes = ", ".join([p.name for p in response.file_paths])
                self.add_message("sistema", f"{response.text}\nArquivos gerados: {nomes}")
            else:
                self.add_message("sistema", response.text)

    def force_extract(self):
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
        except Exception as e:
            self.root.after(0, lambda: self.audio_recognition_callback(None, str(e)))

    def audio_recognition_callback(self, text, error=None):
        self.audio_btn.config(state=tk.NORMAL, text="🎤")
        if error:
            self.add_message("erro", error)
        elif text:
            self.add_message("usuario", f"🎤 {text}")
            response = self.core.process_message(text, user=self.user_context)
            self.add_message("sistema", response.text)

    def run(self):
        self.root.mainloop()

    def __del__(self):
        try:
            self.core.close()
        except Exception:
            pass


if __name__ == "__main__":
    app = WhatsAppFinanceiroApp()
    app.run()