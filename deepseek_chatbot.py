#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Code Assistant - glavni fajl (launcher)
==================================================
Refaktorisan (Faza 1): logika podeljena u chatbot_app/ paket.

- chatbot_app/config.py  : OS detekcija, putanje, settings, modeli, API URL
- chatbot_app/i18n.py    : prevodi (sr/en/zh), ABOUT, SYSTEM_PROMPT
- chatbot_app/utils.py   : ikona, API kljuc, putanje projekta, helperi
- chatbot_app/tools.py   : ToolExecutor + tool definicije
- chatbot_app/widgets.py : DiffDialog

ChatWindow (glavni prozor) ostaje u ovom fajlu - biće izdvojen u Fazi 3.
"""

import sys
import json
import os
import re
import shutil
import glob
import subprocess
import traceback
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox,
    QInputDialog, QDialog, QPlainTextEdit, QSplitter, QFileDialog,
    QDialogButtonBox, QCheckBox, QGroupBox, QFormLayout, QComboBox,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect, QTabWidget, QTextBrowser,
    QButtonGroup, QSlider, QListWidget, QListWidgetItem, QGridLayout
)
from PyQt5.QtCore import Qt, QUrl, QJsonDocument, QTimer, QRect, QPropertyAnimation, QEasingCurve, QEventLoop
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCursor, QTextCharFormat, QIcon, QPixmap, QPainter, QCursor, QFontDatabase
from PyQt5.QtGui import QTextOption

# =============================================================================
# chatbot_app paket - refaktorisani moduli (Faza 1)
# =============================================================================
from chatbot_app.config import (
    APP_NAME, IS_WINDOWS, IS_LINUX, IS_MAC, IS_X11, ICON_EXT, FONT_NAME,
    DEFAULT_FONT, get_data_dir, get_data_file, get_app_dir, DEFAULT_SETTINGS,
    load_settings, save_settings,
    MAX_TOOL_CALLS, MAX_FILES_PER_SESSION, MAX_HISTORY_TOKENS,
    MAX_CONTEXT_TOKENS, MAX_SESSION_HISTORY, KEEP_MESSAGES_ON_SUMMARY,
    PATTERN_DETECT_LIMIT, STREAMING_ENABLED, TEMPERATURE, TOP_P,
    MAX_HISTORY_MESSAGES, HISTORY_FILE, MODELS_CONFIG_FILE, SESSION_FILE,
    load_models_config, save_models_config, FALLBACK_MODELS, DEEPSEEK_MODELS,
    DEFAULT_MODEL, DEEPSEEK_API_URL, DEEPSEEK_BETA_API_URL,
    DEEPSEEK_COMPLETIONS_URL, DEEPSEEK_BETA_COMPLETIONS_URL,
    DEEPSEEK_LIST_MODELS_URL, DEEPSEEK_BALANCE_URL, DEEPSEEK_MODEL,
    DEEPSEEK_SUPPORTED_MODELS, _settings,
)
from chatbot_app.i18n import (
    LANGUAGES, ABOUT_TEXT, LANG_FILE, save_language, load_language, SYSTEM_PROMPT,
)
from chatbot_app.utils import (
    get_deepseek_icon, load_api_key, load_project_path,
    save_project_path, is_within_project, escape_html,
    estimate_tokens, count_context_tokens, short_path,
)
from chatbot_app.tools import TOOLS_DEFINITIONS, ToolExecutor
from chatbot_app.widgets import DiffDialog
from chatbot_app.api_client import validate_and_fix_messages
from chatbot_app.history import HistoryMixin
from chatbot_app.ui.dialogs import DialogsMixin
from chatbot_app.ui.project_context import ProjectContextMixin
from chatbot_app.logger import log, log_time


# =============================================================================
# GLAVNI PROZOR
# =============================================================================

class ChatWindow(QMainWindow, HistoryMixin, DialogsMixin, ProjectContextMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(get_deepseek_icon())
        self.setMinimumSize(600, 500)
        self.resize(900, 650)
        
        # Bez Windows title bara - koristimo custom title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Stanje
        self.api_key = load_api_key()
        self.project_path = load_project_path()
        self.current_lang = load_language()
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._loop_active = False
        self._stop_requested = False  # ⛔ STOP flag
        self._summarize_retry_count = 0  # 🛑 Brojač sažimanja (context limit petlja)
        self._tool_call_count = 0     # Brojač tool callova u petlji
        self._max_tool_calls = MAX_TOOL_CALLS  # Iz settings.json
        self._last_tool_names = []    # 🔄 Poslednjih 7 imena alata za detekciju petlje
        self._recreated_files = set() # 🗑️ Fajlovi koji su kreirani, obrisani pa ponovo kreirani
        self._current_session_id = None  # 📜 ID trenutne sesije u history fajlu (za ažuriranje umesto dupliranja)
        self._pending_tool_results = []
        self.current_model = DEFAULT_MODEL
        self._drag_pos = None  # za pomeranje prozora
        self._is_maximized = False
        self.auto_apply = False  # ⚡ Auto-apply mode (bez pitanja za fajlove)
        self._files_created_in_session = 0  # 📊 Broj kreiranih fajlova u ovoj sesiji
        self._max_files_per_session = MAX_FILES_PER_SESSION  # Iz settings.json
        self._opacity = self._load_opacity()  # 🔍 Providnost prozora (20-100)
        
        # 📡 Streaming state
        self._stream_active = False
        self._stream_buffer = ""
        self._current_stream_content = ""
        self._stream_reply = None
        self._stream_was_active = False  # Flag za _on_api_reply da preskoči streaming reply
        self._stream_block_index = None  # Indeks streaming bloka u dokumentu
        self._show_thinking = _settings.get("show_thinking", True)  # Animacija razmišljanja
        self._thinking_timer = None
        self._thinking_frames = 0
        self._balance_info = self._load_cached_balance()  # Učitaj keširani balans
        self.project_context = ""  # Kontekst projekta (sta je uradjeno)
        self._load_project_context()  # Učitaj kontekst projekta

        # UI
        self._build_ui()

        # Mrežni menadžer (za chat API - trigeruje _on_api_reply)
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self._on_api_reply)

        # 📡 Poseban menadžer za modele/balance (NE trigeruje _on_api_reply)
        self.api_manager = QNetworkAccessManager()

        # Inicijalni prikaz
        self._show_welcome()

        # Ucitaj history ako postoji
        QTimer.singleShot(100, self._load_history)

        # Proveri API ključ - sačekaj da se prozor prikaže
        if not self.api_key:
            QTimer.singleShot(1000, self._ask_for_api_key)
        
        # 🔄 Dohvati modele i balans - sačekaj da se prozor prikaže
        if self.api_key:
            # Prikaži keširani balans odmah
            if self._balance_info and self._balance_info.get("total_balance") != "?":
                bal = self._balance_info
                self.status_label.setText(f"💰 Balans: {bal['total_balance']} {bal['currency']}")
            QTimer.singleShot(1500, self.fetch_models_from_api)
            QTimer.singleShot(3000, self.fetch_user_balance)

    # -------------------------------------------------------------------------
    # POMERANJE PROZORA (frameless drag)
    # -------------------------------------------------------------------------
    def _tr(self, key):
        """Vraća prevedeni tekst za trenutni jezik."""
        return LANGUAGES.get(self.current_lang, LANGUAGES["srpski"]).get(key, key)

    def _on_language_button_clicked(self, lang_key):
        """Menja jezik klikom na taster i osvežava UI."""
        if lang_key == self.current_lang:
            return
        self.current_lang = lang_key
        save_language(self.current_lang)
        # Ažuriraj boje tastera
        for k, btn in self.lang_buttons.items():
            is_active = (k == lang_key)
            bg = "#e94560" if is_active else "#1a1a3e"
            fg = "#ffffff" if is_active else "#a0a0b0"
            border = "#e94560" if is_active else "#2a2a5e"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {fg};
                    border: 1px solid {border};
                    border-radius: 10px;
                    padding: 2px 5px;
                    font-size: 10px;
                    min-width: 24px;
                    max-width: 32px;
                    min-height: 18px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: #e94560;
                    background-color: rgba(233,69,96,0.2);
                }}
            """)
        self._update_ui_texts()
    
    def _update_ui_texts(self):
        """Osvežava tekstove u UI-ju nakon promene jezika."""
        t = self._tr
        self.btn_project.setText(t("open"))
        self.btn_settings.setText(t("key"))
        self.btn_models.setText(t("models"))
        self.btn_history.setText(t("history"))
        self.btn_clear.setText(t("new"))
        self.send_btn.setText(t("send"))
        self.input_field.setPlaceholderText(t("placeholder"))
        self.lbl_hint.setText(t("hint"))
        self.status_label.setText(t("status_ready"))
        # Osveži welcome ako je prazan chat
        if self._loop_active == False and len(self.messages) <= 1:
            self._show_welcome()

    def _title_bar_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def _title_bar_move(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def _title_bar_release(self, event):
        self._drag_pos = None
        event.accept()

    def _toggle_maximize(self):
        if self._is_maximized:
            self.showNormal()
            self._is_maximized = False
            self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            self._is_maximized = True
            self.btn_maximize.setText("❐")

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Custom Title Bar (umesto sive Windows trake) ----
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f3460, stop:1 #1a4a7a);
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(6, 0, 0, 0)
        title_layout.setSpacing(2)

        # Ikonica
        icon_label = QLabel()
        pix = get_deepseek_icon().pixmap(16, 16)
        icon_label.setPixmap(pix)
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("background: transparent;")
        title_layout.addWidget(icon_label)

        # Naziv prozora (drag region)
        title_text = QLabel("DeepSeek assistant by Cole_soft Krusevac")
        title_text.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: 500; background: transparent;")
        title_layout.addWidget(title_text)

        title_layout.addStretch()

        # Title bar buttons
        btn_style = """
            QPushButton {
                background: transparent;
                color: #ffffffcc;
                border: none;
                border-radius: 0px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
                min-width: 28px;
                min-height: 22px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """
        btn_close_style = """
            QPushButton {
                background: transparent;
                color: #ffffffcc;
                border: none;
                border-radius: 0px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
                min-width: 28px;
                min-height: 22px;
            }
            QPushButton:hover {
                background: #e94560;
                color: white;
            }
        """

        self.btn_minimize = QPushButton("─")
        self.btn_minimize.setStyleSheet(btn_style)
        self.btn_minimize.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.btn_minimize)

        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setStyleSheet(btn_style)
        self.btn_maximize.clicked.connect(self._toggle_maximize)
        title_layout.addWidget(self.btn_maximize)

        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet(btn_close_style)
        self.btn_close.clicked.connect(self.close)
        title_layout.addWidget(self.btn_close)

        layout.addWidget(title_bar)

        # Ucini title bar pomerljivim
        title_bar.mousePressEvent = self._title_bar_press
        title_bar.mouseMoveEvent = self._title_bar_move
        title_bar.mouseReleaseEvent = self._title_bar_release
        title_text.mousePressEvent = self._title_bar_press
        title_text.mouseMoveEvent = self._title_bar_move
        title_text.mouseReleaseEvent = self._title_bar_release

        # ---- Toolbar (dva reda) ----
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border-bottom: 1px solid #0f3460; }")
        # toolbar_frame.setMinimumHeight(80)  # Pusti da se sam prilagodi
        toolbar_layout = QVBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(6, 8, 6, 10)
        toolbar_layout.setSpacing(8)

        # Prvi red: jezik, model, key, models, history, new, auto-apply, about, settings, balance
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        row1.setContentsMargins(0, 0, 0, 0)

        # Language buttons
        self.lang_buttons = {}
        self.lang_button_group = QButtonGroup()
        self.lang_button_group.setExclusive(True)
        lang_btn_style_template = """
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 2px 5px;
                font-size: 10px;
                min-width: 24px;
                max-width: 32px;
                min-height: 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: #e94560;
                background-color: rgba(233,69,96,0.2);
            }}
        """
        lang_keys = list(LANGUAGES.keys())
        for i, lang_key in enumerate(lang_keys):
            flag = LANGUAGES[lang_key]["flag"]
            is_active = (lang_key == self.current_lang)
            bg = "#e94560" if is_active else "#16213e"
            fg = "#ffffff" if is_active else "#e0e0e0"
            btn = QPushButton(flag)
            lang_names = {"srpski": "🇷🇸 Srpski", "english": "🇬🇧 English", "中文": "🇨🇳 中文"}
            btn.setToolTip(lang_names.get(lang_key, lang_key))
            btn.setStyleSheet(lang_btn_style_template.format(bg=bg, fg=fg, border="#e94560" if is_active else "#2a2a5e"))
            btn.setCheckable(True)
            btn.setChecked(is_active)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, k=lang_key: self._on_language_button_clicked(k))
            self.lang_buttons[lang_key] = btn
            self.lang_button_group.addButton(btn)
            row1.addWidget(btn)
        
        # Model combo
        self.model_combo = QComboBox()
        self.model_combo.setMaxVisibleItems(10)
        for model_id, model_name in DEEPSEEK_MODELS.items():
            self.model_combo.addItem(model_name, model_id)
        self.model_combo.setCurrentIndex(0)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #16213e;
                color: #e0e0e0;
                border: 1px solid #0f3460;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 140px;
            }
            QComboBox:hover { border-color: #e94560; }
            QComboBox QAbstractItemView {
                background: #16213e;
                color: #e0e0e0;
                selection-background-color: #0f3460;
                selection-color: #e94560;
                border: 1px solid #0f3460;
                outline: none;
                font-size: 11px;
                min-width: 200px;
            }
        """)
        # Model label (klik za promenu) u prvom redu
        self.lbl_model = QPushButton("🧠 " + self.current_model)
        self.lbl_model.setToolTip("Klikni da promeniš model")
        self.lbl_model.setStyleSheet("""
            QPushButton {
                background-color: #16213e;
                color: #e0e0e0;
                border: 1px solid #0f3460;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 140px;
                text-align: left;
            }
            QPushButton:hover {
                border-color: #e94560;
                background-color: #1a2a4e;
            }
        """)
        self.lbl_model.setFixedHeight(26)
        self.lbl_model.clicked.connect(self._show_model_selector)
        row1.addWidget(self.lbl_model)

        self.btn_settings = QPushButton("🔑 Key")
        self.btn_settings.setToolTip("Podesi API ključ")
        self.btn_settings.clicked.connect(self._ask_for_api_key)
        row1.addWidget(self.btn_settings)

        self.btn_models = QPushButton("🧠 Modeli")
        self.btn_models.setToolTip("Dodaj/obriši modele (V5, V6...)")
        self.btn_models.clicked.connect(self._show_models_dialog)
        row1.addWidget(self.btn_models)

        self.btn_history = QPushButton("📜 History")
        self.btn_history.setToolTip("Prikaži sačuvane razgovore")
        self.btn_history.clicked.connect(self._show_history_dialog)
        row1.addWidget(self.btn_history)

        self.btn_clear = QPushButton("🗑️ New")
        self.btn_clear.setToolTip("Započni novi razgovor")
        self.btn_clear.clicked.connect(self._clear_chat)
        row1.addWidget(self.btn_clear)

        # ⚡ Auto-apply toggle
        self.btn_auto_apply = QPushButton("⚡")
        self.btn_auto_apply.setToolTip("Auto-apply: automatski primeni izmene fajlova bez pitanja")
        self.btn_auto_apply.setCheckable(True)
        self.btn_auto_apply.setChecked(False)
        self.btn_auto_apply.setFixedWidth(30)
        self.btn_auto_apply.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e;
                color: #666;
                border: 1px solid #3a3a6e;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                border-color: #e94560;
            }
            QPushButton:checked {
                background-color: #e94560;
                color: white;
                border-color: #e94560;
            }
        """)
        self.btn_auto_apply.toggled.connect(self._on_auto_apply_toggled)
        row1.addWidget(self.btn_auto_apply)

        # Separator
        sep = QLabel("│")
        sep.setStyleSheet("color: #0f3460; font-size: 14px; padding: 0 4px; background: transparent;")
        row1.addWidget(sep)

        self.btn_about = QPushButton("💖")
        self.btn_about.setToolTip("O programu / About / 关于")
        self.btn_about.setFixedWidth(36)
        self.btn_about.clicked.connect(self._show_about)
        self.btn_about.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e94560;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(233,69,96,0.15);
                border-color: #e94560;
            }
        """)
        row1.addWidget(self.btn_about)

        # ⚙️ Settings dugme
        self.btn_settings_config = QPushButton("⚙️")
        self.btn_settings_config.setToolTip("Podesavanja (max tool calls, limiti, istorija)")
        self.btn_settings_config.setFixedWidth(36)
        self.btn_settings_config.clicked.connect(self._show_settings_dialog)
        self.btn_settings_config.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.05);
                border-color: #888;
            }
        """)
        row1.addWidget(self.btn_settings_config)

        # 💰 Balance dugme
        self.btn_balance = QPushButton("💰")
        self.btn_balance.setToolTip("Osveži prikaz balansa")
        self.btn_balance.setFixedWidth(36)
        self.btn_balance.clicked.connect(self.fetch_user_balance)
        self.btn_balance.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #4CAF50;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(76,175,80,0.15);
                border-color: #4CAF50;
            }
        """)
        row1.addWidget(self.btn_balance)

        toolbar_layout.addLayout(row1)

        # Drugi red: project path i Open dugme
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        
        self.lbl_project = QLabel("📁 " + self._short_path(self.project_path, 50))
        self.lbl_project.setStyleSheet("color: #888; font-size: 12px; padding: 6px 6px; background: transparent; min-height: 20px;")
        self.lbl_project.setFixedHeight(28)
        row2.addWidget(self.lbl_project)
        
        row2.addStretch()
        
        self.btn_project = QPushButton("📂 Open")
        self.btn_project.setToolTip("Promeni projektni direktorijum")
        self.btn_project.setFixedHeight(28)
        self.btn_project.clicked.connect(self._choose_project_path)
        row2.addWidget(self.btn_project)
        
        toolbar_layout.addLayout(row2)
        layout.addWidget(toolbar_frame)

        # ---- Chat display ----
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #16213e;
                color: #e0e0e0;
                border: none;
                padding: 12px;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.chat_display, stretch=1)

        # ---- Status bar ----
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border-top: 1px solid #0f3460; }")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 4, 12, 4)

        self.status_label = QLabel("✅ Spreman")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # 🔍 Transparency slider (donji desni ugao)
        self.opacity_label = QLabel("🔆")
        self.opacity_label.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
        self.opacity_label.setToolTip("Providnost prozora")
        status_layout.addWidget(self.opacity_label)

        # Procenat pored klizača (MORA pre sliders da bi _on_opacity_changed radio)
        self.opacity_pct = QLabel(f"{self._opacity}%")
        self.opacity_pct.setStyleSheet("color: #888; font-size: 10px; min-width: 32px; background: transparent;")
        status_layout.addWidget(self.opacity_pct)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.setToolTip("Podesi providnost prozora")
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a4e;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #e94560;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #e94560;
                border-radius: 2px;
            }
            QSlider:hover::handle:horizontal {
                background: #ff6b6b;
                width: 14px;
                height: 14px;
                margin: -5px 0;
            }
        """)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.opacity_slider.setValue(self._opacity)  # ovo će trigerovati _on_opacity_changed
        status_layout.addWidget(self.opacity_slider)

        # Status indikator
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #6a9955; font-size: 8px; background: transparent;")
        status_layout.addWidget(status_dot)

        layout.addWidget(status_frame)

        # ---- Input area ----
        input_frame = QWidget()
        input_frame.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                border-top: 1px solid #0f3460;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 10, 12, 12)
        input_layout.setSpacing(4)

        # Input row
        row = QHBoxLayout()
        row.setSpacing(6)

        # 💭 Thinking toggle levo od input polja
        self.btn_thinking = QPushButton("🧠")
        self.btn_thinking.setToolTip("Prikaži/sakrij AI razmišljanje (čitanje fajlova, pretrage, komande)")
        self.btn_thinking.setCheckable(True)
        self.btn_thinking.setChecked(self._show_thinking)
        self.btn_thinking.toggled.connect(self._on_thinking_toggled)
        self.btn_thinking.setFixedWidth(32)
        self.btn_thinking.setFixedHeight(32)
        self.btn_thinking.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: 2px solid #3a3a5e;
                border-radius: 8px;
                padding: 0px;
                font-size: 14px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton:hover {
                border-color: #888;
                background: rgba(255,255,255,0.05);
            }
            QPushButton:checked {
                background: rgba(233,69,96,0.2);
                color: #e94560;
                border-color: #e94560;
            }
        """)
        row.addWidget(self.btn_thinking)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Napiši šta treba uraditi... (Enter = pošalji)")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #16213e;
                color: #e0e0e0;
                border: 2px solid #0f3460;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
                selection-background-color: #e94560;
            }
            QLineEdit:focus {
                border-color: #e94560;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send_or_stop)
        row.addWidget(self.input_field)

        # 😊 Emoji dugme
        self.btn_emoji = QPushButton("😊")
        self.btn_emoji.setToolTip("Ubaci emoji")
        self.btn_emoji.setFixedWidth(36)
        self.btn_emoji.setFixedHeight(32)
        self.btn_emoji.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaa;
                border: 2px solid #3a3a5e;
                border-radius: 8px;
                padding: 0px;
                font-size: 16px;
            }
            QPushButton:hover {
                border-color: #e94560;
                background: rgba(255,255,255,0.05);
            }
        """)
        self.btn_emoji.clicked.connect(self._show_emoji_picker)
        row.addWidget(self.btn_emoji)

        self.send_btn = QPushButton("▶ Pošalji")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #ff6b6b);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:1 #ff8e8e);
            }
            QPushButton:pressed {
                background: #c73e55;
            }
            QPushButton:disabled {
                background: #3a3a4e;
                color: #666;
            }
        """)
        self.send_btn.clicked.connect(self._on_send_or_stop)
        row.addWidget(self.send_btn)

        input_layout.addLayout(row)

        # Hint
        self.lbl_hint = QLabel("💡 Npr: 'pokaži main.cpp', 'popravi grešku', 'nađi QString', 'dodaj funkciju'")
        self.lbl_hint.setStyleSheet("color: #555; font-size: 10px; padding: 2px 4px; background: transparent;")
        input_layout.addWidget(self.lbl_hint)

        layout.addWidget(input_frame)

        # Primeni trenutni jezik na sve tekstove
        self._update_ui_texts()

    # -------------------------------------------------------------------------
    # PRIKAZ PORUKA
    # -------------------------------------------------------------------------
    def _show_welcome(self):
        t = self._tr
        self.chat_display.setHtml(f"""
<div style="text-align: center; color: #888; padding: 30px;">
    <h1 style="color: #ccc;">{t('welcome_title')}</h1>
    <p style="font-size: 13px;">{t('welcome_sub')}</p>
    <hr style="border-color: #444; width: 40%;">
    <p style="font-size: 11px; color: #666;">
        📁 {t('project')} {self._short_path(self.project_path, 50)}<br>
        💡 {t('welcome_hint')}
    </p>
</div>
""")
        self.chat_display.append("")

    def _append_system_message(self, text):
        """Dodaje sistemsku poruku u chat (npr. obaveštenje o kreiranju/izmeni fajla)."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        html = f'<div style="margin: 4px 20px; padding: 6px 10px; background-color: #1a1a3e; border-left: 3px solid #e94560; border-radius: 4px; font-size: 11px; color: #d4b8ff;">{text}</div><br>'
        cursor.insertHtml(html)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        if self.input_field.isEnabled():
            QTimer.singleShot(10, self.input_field.setFocus)

    def _append_message(self, role, text_html):
        """Dodaje poruku u chat display sa alignment-om (user desno, AI levo)."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Ako je poslednji placeholder "razmišljam...", ukloni ga
        doc = self.chat_display.document()
        last_block = doc.lastBlock().text()
        if "razmišljam" in last_block:
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        cursor.movePosition(QTextCursor.End)

        if role == "user":
            # Korisnik levo
            html = (
                '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                '<td style="background-color:#264f78; color:#fff; '
                'border-radius:8px; padding:8px 12px;">'
                '<b style="color:#89b4fa; font-size:11px;">👤 Ti</b><br>'
                + text_html +
                '</td>'
                '<td width="30%"></td>'
                '</tr></table>'
            )
        elif role == "assistant":
            # DeepSeek desno
            html = (
                '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                '<td width="30%"></td>'
                '<td style="background-color:#2d2d2d; color:#d4d4d4; '
                'border-radius:8px; padding:8px 12px;">'
                '<b style="color:#6a9955; font-size:11px;">🤖 DeepSeek</b><br>'
                + text_html +
                '</td>'
                '</tr></table>'
            )
        elif role == "tool_call":
            if not self._show_thinking:
                return  # Sakrij ako je thinking isključen
            html = '<div style="margin: 4px 20px; padding: 4px 8px; background-color: #2d2d2d; border-left: 3px solid #dcdcaa; font-size: 11px; color: #dcdcaa;">' + text_html + '</div>'
        elif role == "tool_result":
            if not self._show_thinking:
                return  # Sakrij ako je thinking isključen
            html = '<div style="margin: 4px 20px; padding: 4px 8px; background-color: #1e2e1e; border-left: 3px solid #6a9955; font-size: 11px;">' + text_html + '</div>'
        elif role == "error":
            html = '<div style="margin: 4px 0; color: #f44747;">' + text_html + '</div>'
        elif role == "thinking":
            html = '<div style="margin: 4px 40px; color: #888; font-style: italic; text-align: center;">⏳ ' + text_html + '</div>'
        else:
            html = '<div style="margin: 4px 0;">' + text_html + '</div>'

        cursor.insertHtml(html)
        cursor.insertHtml('<br>')

        # Scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        # ⭐️ Vrati fokus na input posle dodavanja poruke (scroll ne sme da ga ukrade)
        if self.input_field.isEnabled():
            QTimer.singleShot(10, self.input_field.setFocus)

    def _escape_html(self, text):
        """Wrapper - logika u chatbot_app.utils.escape_html."""
        return escape_html(text)

    def _short_path(self, path, max_len=40):
        """Wrapper - logika u chatbot_app.utils.short_path."""
        return short_path(path, max_len)

    # -------------------------------------------------------------------------
    # ⛔ STOP / SLANJE PORUKE (isto dugme)
    # -------------------------------------------------------------------------
    def _on_send_or_stop(self):
        """Kad se klikne na dugme: šalje poruku ILI zaustavlja AI."""
        if self._loop_active:
            self._stop_ai_loop()
        else:
            self._send_message()

    def _stop_ai_loop(self):
        """Hitno prekida AI petlju."""
        self._stop_requested = True
        self._loop_active = False
        self._stream_active = False  # Prekini streaming
        
        # Abortuj streaming reply ako postoji
        if self._stream_reply:
            try:
                self._stream_reply.abort()
            except:
                pass
            self._stream_reply = None
        
        self._update_send_button(is_running=False)
        self._set_ui_enabled(True)
        self.status_label.setText("⛔ Prekinuto")
        self._stop_thinking_animation()
        self._stream_block_position = None
        self._append_message("error", "⛔ <b>STOP</b> - korisnik je prekinuo AI petlju.")
        # Otkaži sve pending zahteve (novi manager)
        self.manager.blockSignals(True)
        old_manager = self.manager
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self._on_api_reply)
        old_manager.deleteLater()

    def _update_send_button(self, is_running):
        """Menja izgled dugmeta: ▶ Pošalji / ⛔ STOP."""
        if is_running:
            self.send_btn.setText("⛔ STOP")
            self.send_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #c0392b, stop:1 #e74c3c);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e74c3c, stop:1 #ff6b6b);
                }
                QPushButton:pressed {
                    background: #a93226;
                }
                QPushButton:disabled {
                    background: #3a3a4e;
                    color: #666;
                }
            """)
        else:
            self.send_btn.setText("▶ Pošalji")
            self.send_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e94560, stop:1 #ff6b6b);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff6b6b, stop:1 #ff8e8e);
                }
                QPushButton:pressed {
                    background: #c73e55;
                }
                QPushButton:disabled {
                    background: #3a3a4e;
                    color: #666;
                }
            """)

    def _send_message(self):
        log("📤 _send_message() - korisnik poslao poruku")
        if self._loop_active:
            return
        
        # ⛔ Ne dozvoli slanje dok se modeli učitavaju
        if self.current_model == "loading":
            self._append_message("error", "⏳ <b>Sačekaj da se modeli učitaju sa API-ja...</b>")
            self.status_label.setText("⏳ Modeli se učitavaju...")
            return

        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self._append_message("user", self._escape_html(user_text))
        self.input_field.clear()

        self.messages.append({"role": "user", "content": user_text})

        # 🔄 Sažmi history ako je prevelik
        self._summarize_history()
        
        # 📝 Dodaj SAŽETAK konteksta projekta u system prompt ako postoji i nije već dodat
        if self.project_context and len(self.messages) <= 2:
            # ⚠️ Umesto celog fajla (30KB) šaljemo samo sažetak poslednjih unosa
            ctx_summary = self._get_project_context_summary()
            if ctx_summary:
                ctx_msg = f"\n\n{ctx_summary}\n\nNastavi rad na projektu na osnovu gore navedenog konteksta."
                existing_content = self.messages[0].get("content", "")
                self.messages[0]["content"] = existing_content + ctx_msg

        # ⛔ Reset stop state
        self._stop_requested = False
        self._tool_call_count = 0
        self._last_tool_names = []     # Reset praćenja patterna
        self._recreated_files = set()  # Reset praćenja fajlova
        self._retry_length_count = 0   # Reset retry brojača za finish_reason="length"
        self._summarize_retry_count = 0  # 🛑 Reset brojača sažimanja (context limit petlja)

        self._loop_active = True
        self._update_send_button(is_running=True)
        self._call_api()

    def _summarize_history(self):
        """Sažima istoriju ako je previše narasla.
        Čuva system prompt, poslednjih N poruka (UKLJUČUJUĆI tool poruke),
        a starije zamenjuje sažetkom.
        
        ⚠️ VAŽNO: Čuva tool poruke uz njihove assistant tool_calls poruke!
        Ako sačuvamo assistant poruku sa tool_calls, moramo sačuvati i
        odgovarajuće tool poruke, inače API vraća 400 grešku.
        
        ⚠️ VAŽNO #2: Sažimanje se pokreće kad total_tokens pređe MAX_HISTORY_TOKENS (8000).
        Ako sačekamo MAX_CONTEXT_TOKENS (800000), kontekst će biti prevelik za API.
        """
        log("🔄 _summarize_history() - provera")
        # Prvo proveri da li uopšte treba sažimati
        total_tokens = count_context_tokens(self.messages)
        
        if total_tokens < MAX_HISTORY_TOKENS:
            return False  # Nije potrebno sažimanje
        # Ako je preko MAX_HISTORY_TOKENS, sažimamo - ne čekamo MAX_CONTEXT_TOKENS!
        
        self._save_history()  # Sačuvaj pre sažimanja
        
        # System prompt je uvek na indexu 0
        system_prompt = self.messages[0]
        
        # Uzmi poslednjih KEEP_MESSAGES_ON_SUMMARY poruka (sve role: user, assistant, tool)
        recent = []
        # Prvo uzmi poslednjih N poruka (bez obzira na rolu)
        for msg in reversed(self.messages[1:]):  # Preskoči system prompt
            recent.insert(0, msg)
            if len(recent) >= KEEP_MESSAGES_ON_SUMMARY:
                break
        
        # ⚠️ VAŽNO: Proveri da li ima "visećih" tool_calls (assistant sa tool_calls
        # bez odgovarajućih tool poruka na KRAJU recent liste)
        # Ako poslednja poruka u recent ima tool_calls, moramo uključiti
        # i tool poruke koje joj slede (one su izvan recent granice)
        # Ovo se rešava tako što uvijek čuvamo kompletan krug
        
        # 🔍 Proveri da li PRVA poruka u recent ima "tool" rolu.
        # Ako da, znači da je assistant(tool_calls) poruka odsečena,
        # što bi izazvalo Error 400 ("tool" bez "tool_calls" pretka).
        if recent and recent[0].get("role") == "tool":
            # Nađi odgovarajuću assistant(tool_calls) poruku u originalnim messages
            first_idx = None
            for i, msg in enumerate(self.messages):
                if msg is recent[0]:
                    first_idx = i
                    break
            if first_idx is not None and first_idx > 0:
                # Idi unazad da nađeš assistant poruku sa tool_calls
                for k in range(first_idx - 1, -1, -1):
                    prev = self.messages[k]
                    if prev.get("role") == "assistant" and prev.get("tool_calls"):
                        if prev not in recent:
                            recent.insert(0, prev)
                        break
        
        # Pronađi u originalnim messages gde se nalazi poslednja poruka iz recent
        last_recent_msg = recent[-1] if recent else None
        if last_recent_msg:
            # Nadji index poslednje poruke u originalnim messages
            for i, msg in enumerate(self.messages):
                if msg is last_recent_msg:
                    # Dodaj sve poruke posle nje koje su "tool" role
                    # (pripadaju istoj tool rundi)
                    j = i + 1
                    while j < len(self.messages) and self.messages[j].get("role") == "tool":
                        if self.messages[j] not in recent:
                            recent.append(self.messages[j])
                        j += 1
                    break
        
        session_summary = f"\n\n[History summary: Previous conversation had {len(self.messages)-1} messages. Only the last {len(recent)} messages are preserved. Older context was saved to history file.]"
        
        # ⚠️ Spoji summary sa postojećim system promptom!
        # DeepSeek API NE podržava dve uzastopne system poruke - to izaziva prazan odgovor!
        original_content = system_prompt.get("content", "") if system_prompt else ""
        merged_system = dict(system_prompt)
        merged_system["content"] = original_content + session_summary
        
        self.messages = [merged_system]
        
        # ⚠️ VAŽNO #3: SKRATI sadržaj svake sačuvane poruke!
        # Problem: poslednjih 10 poruka mogu biti ogromne (tool rezultati sa celim
        # fajlovima, dugi AI odgovori) - i dalje prelaze context limit, pa API
        # vraća 400 u BESKONAČNOJ PETLJI.
        # Rešenje: skrati svaku poruku na razumnu dužinu.
        # ⚠️ KRITIČNO: pravimo KOPIJE poruka! Ako menjamo originalne poruke
        # (koje su reference u self.messages), sažeti razgovor se zauvek skrati
        # i u history fajlu - korisnik vidi "XXXX... [skraćeno]" umesto pravog teksta!
        MAX_MSG_CHARS = {
            "user": 2000,       # korisničke poruke su obično kratke
            "assistant": 3000,  # AI odgovor - zadrži suštinu
            "tool": 500,        # tool rezultati - samo prvi deo (bio je ogroman!)
            "system": 4000,     # system prompt (sažetak) - ograniči
        }
        recent_copies = []
        for msg in recent:
            # 📋 Napravi KOPIJU - original u self.messages/history ostaje netaknut!
            msg_copy = dict(msg)
            role = msg_copy.get("role", "")
            content = msg_copy.get("content", "")
            if isinstance(content, str):
                limit = MAX_MSG_CHARS.get(role, 2000)
                if len(content) > limit:
                    msg_copy["content"] = content[:limit] + f"\n... [skraćeno sa {len(content)} na {limit} chars]"
            recent_copies.append(msg_copy)
        
        self.messages.extend(recent_copies)
        
        # ⚠️ VAŽNO #4: Ako i posle skraćivanja i dalje prelazi limit,
        # obriši tool poruke (najveće su - sadrže cele fajlove).
        # Tool poruke nisu kritične za nastavak razgovora.
        total_after = count_context_tokens(self.messages)
        if total_after > MAX_HISTORY_TOKENS * 2:  # sigurnosna granica
            log(f"⚠️ Nakon skraćivanja i dalje {total_after} tokena - brišem tool poruke")
            self.messages = [m for m in self.messages if m.get("role") != "tool"]
            # Proveri ponovo - ako i dalje prelazi, smanji broj poruka na 5
            total_after2 = count_context_tokens(self.messages)
            if total_after2 > MAX_HISTORY_TOKENS * 2 and len(self.messages) > 3:
                log(f"⚠️ I dalje {total_after2} tokena - ostavljam samo poslednjih 5 poruka")
                self.messages = [self.messages[0]] + self.messages[-5:]
        
        self._append_system_message(
            f"🔄 <b>History sažet:</b> {total_tokens:,} tokena → {len(recent)} poslednjih poruka sačuvano. "
            f"Stariji deo je sačuvan u history fajlu."
        )
        self.status_label.setText(f"🔄 History sažet: {total_tokens:,} → {len(recent)} poruka")
        log(f"🔄 _summarize_history() - sazet: {total_tokens:,} → {len(recent)} poruka")
        return True

    def _on_auto_apply_toggled(self, checked):
        """Kad se uključi/isključi auto-apply mod."""
        if checked:
            # ⚠️ Upozorenje pre uključivanja
            reply = QMessageBox.warning(self, "⚠️ Auto-apply",
                "⚡ <b>Auto-apply uključen!</b>\n\n"
                "AI će kreirati i menjadi fajlove <b>bez tvoje potvrde</b>.\n\n"
                f"📊 Maksimalno <b>{self._max_files_per_session} fajlova</b> po sesiji.\n"
                "Posle toga se auto-apply automatski isključuje.\n\n"
                "⚠️ Pritisni ⛔ STOP ako AI pobegne u petlju!",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                self.btn_auto_apply.setChecked(False)
                return
            self.auto_apply = True
            self._files_created_in_session = 0  # Reset brojača
            self.status_label.setText(f"⚡ Auto-apply: UKLJUČEN (0/{self._max_files_per_session})")
            self.btn_auto_apply.setToolTip(f"Auto-apply UKLJUČEN ({self._files_created_in_session}/{self._max_files_per_session})")
        else:
            self.auto_apply = False
            self.status_label.setText(self._tr("status_ready"))
            self.btn_auto_apply.setToolTip("Auto-apply: automatski primeni izmene fajlova bez pitanja")

    def _show_model_selector(self):
        """Otvara mali prozor za izbor modela umesto combo box-a."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Izaberi model")
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(4, 4, 4, 4)
        
        list_widget = QListWidget()
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: #16213e;
                color: #e0e0e0;
                border: none;
                outline: none;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #1a2a4e;
            }
            QListWidget::item:selected {
                background-color: #0f3460;
                color: #e94560;
            }
        """)
        
        for model_id, model_name in DEEPSEEK_MODELS.items():
            item = QListWidgetItem(f"{model_name} ({model_id})")
            item.setData(Qt.UserRole, model_id)
            if model_id == self.current_model:
                item.setSelected(True)
            list_widget.addItem(item)
        
        list_widget.itemClicked.connect(lambda item: self._on_model_selected(item, dlg))
        layout.addWidget(list_widget)
        
        # Pozicioniraj ispod lbl_model
        btn_pos = self.lbl_model.mapToGlobal(self.lbl_model.rect().bottomLeft())
        dlg.move(btn_pos)
        dlg.setFixedWidth(300)
        dlg.exec_()
    
    def _show_emoji_picker(self):
        """Otvara prozor sa emoji izborom."""
        emoji_data = {
            "😊 Smajlići": [
                "😀","😁","😂","🤣","😃","😄","😅","😆","😉","😊",
                "😋","😎","😍","🥰","😘","😗","😙","😚","🙂","🤗",
                "🤩","🤔","🤨","😐","😑","😶","🙄","😏","😣","😥",
                "😮","🤐","😯","😪","😫","😴","😌","😛","😜","😝",
                "🤤","😒","😓","😔","😕","🙃","🤑","😲","☹️","😞",
                "😟","😤","😢","😭","😦","😧","😨","😩","🤯","😬",
                "😰","😱","🥵","🥶","😳","🤪","😵","😡","😠","🤬",
                "😈","👿","💀","☠️","💩","🤡","👹","👺","👻","👽"
            ],
            "👍 Gestikulacije": [
                "👍","👎","👊","✊","🤛","🤜","👏","🙌","👐","🤲",
                "🤝","🙏","✌️","🤞","🤟","🤘","👌","✋","🤚","🖐️",
                "🖖","👋","🤙","💪","🦵","🦶","👂","🦻","👃","🧠",
                "🦷","🦴","👀","👁️","👅","👄","💋","🫂","🤳","💅"
            ],
            "❤️ Simboli": [
                "❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💕",
                "💞","💓","💗","💖","💘","💝","💟","❣️","💔","❤️‍🔥",
                "❤️‍🩹","💯","💢","💥","💫","💦","💨","🕳️","💬","🗨️",
                "🗯️","💭","💤","⭐","🌟","✨","⚡","🔥","💧","🌊"
            ],
            "🎉 Objekti": [
                "🎉","🎊","🎈","🎁","🎀","🪅","🪆","🎃","🎄","🎆",
                "🎇","🧨","✨","🎭","🎨","🎪","🎤","🎧","🎼","🎹",
                "🥁","🎷","🎺","🎸","🪕","🎻","🎲","♟️","🎯","🎳",
                "🎮","🕹️","📱","💻","🖥️","🖨️","⌨️","🖱️","🖲️","📷",
                "📹","📼","🔍","🔎","🕯️","💡","🔦","🏮","📔","📕",
                "📖","📗","📘","📙","📚","📓","📃","📜","📄","📰",
                "🗞️","📑","🔖","🏷️","💰","💴","💵","💶","💷","💸",
                "💳","🧾","✉️","📧","📨","📩","📤","📥","📦","📫",
                "📪","📬","📭","📮","🗳️","✏️","✒️","🖊️","🖋️","🖌️",
                "🖍️","📝","📁","📂","🗂️","📅","📆","🗒️","🗓️","📇",
                "📈","📉","📊","📋","📌","📍","📎","🖇️","📏","📐",
                "🔒","🔓","🔏","🔐","🔑","🗝️","🔨","🪓","⛏️","⚒️",
                "🛠️","🗡️","⚔️","🔫","🪃","🏹","🛡️","🔧","🔩","⚙️",
                "🗜️","⚖️","🦯","🔗","⛓️","🧰","🧲","🪜","⚗️","🧪",
                "🧫","🧬","🔬","🔭","📡","💉","🩸","💊","🩹","🩺"
            ]
        }
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Izaberi emoji")
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-radius: 6px;
            }
        """)
        dlg.setFixedSize(480, 400)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background: #16213e;
                border: 1px solid #0f3460;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #1a1a3e;
                color: #888;
                border: 1px solid #0f3460;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-height: 24px;
            }
            QTabBar::tab:selected {
                background: #16213e;
                color: #e94560;
                border-color: #0f3460;
            }
            QTabBar::tab:hover {
                background: #2a2a4e;
            }
        """)
        
        for tab_name, emojis in emoji_data.items():
            browser = QTextBrowser()
            browser.setReadOnly(True)
            browser.setOpenExternalLinks(False)
            browser.setStyleSheet("""
                QTextBrowser {
                    background: #16213e;
                    color: #ffffff;
                    border: none;
                    font-size: 28px;
                    padding: 8px;
                }
            """)
            
            # HTML za emoji - svaki kao link sa unicode kodom
            html_parts = ['<div style="font-size: 28px; line-height: 2.0; letter-spacing: 6px; text-align: center;">']
            for idx, emoji_char in enumerate(emojis):
                html_parts.append(f'<a href="emoji:{idx}" style="text-decoration:none; color:#ffffff; padding:3px 6px;">{emoji_char}</a>')
            html_parts.append('</div>')
            
            browser.setHtml(''.join(html_parts))
            
            def on_anchor(url, d=dlg, emoji_list=emojis):
                if url.scheme() == "emoji":
                    idx_str = url.path()
                    if idx_str.startswith("/"):
                        idx_str = idx_str[1:]
                    try:
                        idx = int(idx_str)
                        if 0 <= idx < len(emoji_list):
                            self._insert_emoji(emoji_list[idx], d)
                    except:
                        pass
            
            browser.anchorClicked.connect(on_anchor)
            tabs.addTab(browser, tab_name)
        
        layout.addWidget(tabs)
        
        # Pozicioniraj IZNAD dugmeta (da ne ispada dole van ekrana)
        btn_global = self.btn_emoji.mapToGlobal(self.btn_emoji.rect().topLeft())
        dlg.move(btn_global.x(), btn_global.y() - dlg.height() - 5)
        
        dlg.exec_()
    
    def _insert_emoji(self, emoji, dlg):
        """Ubacuje emoji u polje za unos."""
        current_text = self.input_field.text()
        cursor = self.input_field.cursorPosition()
        new_text = current_text[:cursor] + emoji + current_text[cursor:]
        self.input_field.setText(new_text)
        self.input_field.setCursorPosition(cursor + len(emoji))
        self.input_field.setFocus()
        dlg.accept()
    
    def _on_model_selected(self, item, dlg):
        """Kad korisnik izabere model iz liste."""
        model_id = item.data(Qt.UserRole)
        if model_id and model_id in DEEPSEEK_MODELS:
            self.current_model = model_id
            self.lbl_model.setText("🧠 " + model_id)
            self._on_model_changed_silent(model_id)
        dlg.accept()
    
    def _on_model_changed_silent(self, model_id):
        """Ažurira status bez promene combo box-a."""
        is_r1 = "reasoner" in model_id or "r1" in model_id.lower()
        if is_r1:
            self.status_label.setText(
                f"🧠 Model: {model_id} ({DEEPSEEK_MODELS[model_id]}) ⚠️ R1 NE podržava "
                f"'required' tool_choice - alati rade u 'auto' režimu"
            )
        else:
            self.status_label.setText(f"🧠 Model: {model_id} ({DEEPSEEK_MODELS[model_id]})")
        print(f"[DeepSeek] Promenjen model na: {model_id}")

    def _load_cached_balance(self):
        """Učitava keširani balans iz fajla."""
        try:
            path = get_data_file("balance_cache.txt")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
        except:
            pass
        return {"total_balance": "?", "currency": "CNY", "is_available": False, "last_updated": "nikad"}

    def _on_thinking_toggled(self, checked):
        """Uključuje/isključuje prikaz AI razmišljanja (tool calls)."""
        self._show_thinking = checked
        if not checked:
            self._stop_thinking_animation()
        settings = load_settings()
        settings["show_thinking"] = checked
        save_settings(settings)
        self.status_label.setText("🧠 Thinking: " + ("ON" if checked else "OFF"))

    def _on_opacity_changed(self, value):
        """Menja providnost prozora (20% = skoro providno, 100% = potpuno vidljivo)."""
        self._opacity = value
        opacity_float = value / 100.0
        self.setWindowOpacity(opacity_float)
        self.opacity_pct.setText(f"{value}%")
        # Sačuvaj podešavanje
        self._save_opacity(value)
        # Ažuriraj tooltip
        if value < 50:
            hint = "😎 Stealth mode"
        elif value < 80:
            hint = "👀 Poluprovidno"
        else:
            hint = "💪 Puno vidljivo"
        self.opacity_slider.setToolTip(f"Providnost: {value}% - {hint}")

    def _save_opacity(self, value):
        """Čuva providnost u fajl."""
        try:
            with open(get_data_file("opacity.txt"), "w") as f:
                f.write(str(value))
        except:
            pass

    def _load_opacity(self):
        """Učitava providnost iz fajla. Default: 100."""
        try:
            path = get_data_file("opacity.txt")
            if os.path.exists(path):
                with open(path, "r") as f:
                    val = int(f.read().strip())
                    return max(20, min(100, val))
        except:
            pass
        return 100

    def _on_model_changed(self, index):
        model_id = self.model_combo.itemData(index)
        if not model_id:
            return
        # Preskoči placeholder "loading" model
        if model_id == "loading":
            return
        if model_id in DEEPSEEK_MODELS:
            self.current_model = model_id
            # Ažuriraj labelu ako postoji
            if hasattr(self, 'lbl_model'):
                self.lbl_model.setText("🧠 " + model_id)
            # ⚠️ Proveri da li je R1 - ne podržava forced tools
            is_r1 = "reasoner" in model_id or "r1" in model_id.lower()
            if is_r1:
                self.status_label.setText(
                    f"🧠 Model: {model_id} ({DEEPSEEK_MODELS[model_id]}) ⚠️ R1 NE podržava "
                    f"'required' tool_choice - alati rade u 'auto' režimu"
                )
            else:
                self.status_label.setText(f"🧠 Model: {model_id} ({DEEPSEEK_MODELS[model_id]})")
            print(f"[DeepSeek] Promenjen model na: {model_id}")

    # =========================================================================
    # 🔄 API: Dohvatanje modela sa https://api.deepseek.com/list-models
    # =========================================================================
    def fetch_models_from_api(self):
        """Dohvata listu dostupnih modela sa DeepSeek API-ja."""
        log("🔃 fetch_models_from_api() - krece")
        if not self.api_key:
            return
        if not self.isVisible():
            QTimer.singleShot(200, self.fetch_models_from_api)
            return
        
        try:
            self.status_label.setText("🔄 Dohvatam modele sa API-ja...")
            url = QUrl(DEEPSEEK_LIST_MODELS_URL)
            request = QNetworkRequest(url)
            request.setRawHeader(b"Authorization", f"Bearer {self.api_key}".encode("utf-8"))
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            
            reply = self.api_manager.get(request)
            reply.finished.connect(lambda: self._on_models_api_reply(reply))
        except Exception as e:
            print(f"[DeepSeek] Greška pri dohvatanju modela: {e}")
            self._apply_models(FALLBACK_MODELS)
    
    def _on_models_api_reply(self, reply):
        """Obradjuje odgovor od /models API-ja."""
        try:
            if reply.error() != QNetworkReply.NoError:
                err_msg = reply.errorString()
                print(f"[DeepSeek] Greška pri dohvatanju modela: {err_msg}")
                print("[DeepSeek] Koristim fallback modele")
                self._apply_models(FALLBACK_MODELS)
                self.status_label.setText("✅ Učitani lokalni modeli (API nema list-models)")
                reply.deleteLater()
                return
            
            data_bytes = reply.readAll().data()
            data = json.loads(data_bytes)
            
            # ✅ Parsiraj odgovor: {"object":"list","data":[{"id":"deepseek-chat","object":"model",...}]}
            models_data = data.get("data", [])
            if not models_data:
                print("[DeepSeek] API nije vratio modele, koristim fallback")
                self._apply_models(FALLBACK_MODELS)
                self.status_label.setText("✅ Učitani lokalni modeli (API prazan)")
                reply.deleteLater()
                return
            
            # Konvertuj u naš format
            new_models = []
            known_names = {
                "deepseek-chat": "DeepSeek V3",
                "deepseek-reasoner": "DeepSeek R1",
                "deepseek-v4": "DeepSeek V4",
                "deepseek-v4-flash": "DeepSeek V4 Flash",
                "deepseek-coder": "DeepSeek Coder",
                "deepseek-coder-v2": "DeepSeek Coder V2",
            }
            
            for m in models_data:
                model_id = m.get("id", "")
                if not model_id:
                    continue
                if not model_id.startswith("deepseek"):
                    continue
                name = known_names.get(model_id, model_id.replace("-", " ").title())
                new_models.append({"id": model_id, "name": name})
            
            if not new_models:
                print("[DeepSeek] API nema DeepSeek modela, koristim fallback")
                self._apply_models(FALLBACK_MODELS)
                self.status_label.setText("✅ Učitani lokalni modeli (API nema DeepSeek modela)")
                reply.deleteLater()
                return
            
            self._apply_models(new_models)
            count = len(new_models)
            self.status_label.setText(f"✅ Učitano {count} modela sa API-ja")
            self._append_system_message(
                f"🔄 <b>Modeli ažurirani sa API-ja:</b> {count} modela "
                f"(prvi: {new_models[0]['id']})"
            )
            
        except Exception as e:
            print(f"[DeepSeek] Greška pri parsiranju modela: {e}")
            print("[DeepSeek] Koristim fallback modele")
            self._apply_models(FALLBACK_MODELS)
            self.status_label.setText("✅ Učitani lokalni modeli (greška API-ja)")
        
        try:
            reply.deleteLater()
        except:
            pass
    
    def _apply_models(self, models):
        """Primenjuje listu modela na combo box i globalne promenljive."""
        global DEEPSEEK_MODELS, DEFAULT_MODEL
        if not models:
            models = FALLBACK_MODELS
        
        # Označi prvi kao default ako nijedan nije označen
        has_default = any(m.get("default") for m in models)
        if not has_default and models:
            models[0]["default"] = True
            for m in models[1:]:
                m["default"] = False
        
        # Sačuvaj u fajl
        save_models_config(models)
        
        # Ažuriraj globalne
        DEEPSEEK_MODELS = {m["id"]: m["name"] for m in models}
        DEFAULT_MODEL = next((m["id"] for m in models if m.get("default")), models[0]["id"])
        
        # Ažuriraj combo box (zadrži trenutni model ako postoji)
        current_id = self.current_model
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        found_current = False
        for model_data in models:
            self.model_combo.addItem(model_data["name"], model_data["id"])
            if model_data["id"] == current_id:
                found_current = True
        
        if found_current:
            idx = self.model_combo.findData(current_id)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        else:
            self.current_model = DEFAULT_MODEL
            self.model_combo.setCurrentIndex(0)
        
        self.model_combo.blockSignals(False)
    
    # =========================================================================
    # 💰 API: Dohvatanje balansa sa https://api.deepseek.com/get-user-balance
    # =========================================================================
    def fetch_user_balance(self):
        """Dohvata preostali kredit sa DeepSeek API-ja."""
        log("💰 fetch_user_balance() - krece")
        if not self.api_key:
            return
        if not self.isVisible():
            QTimer.singleShot(500, self.fetch_user_balance)
            return
        
        try:
            self.status_label.setText("💰 Dohvatam balans...")
            url = QUrl(DEEPSEEK_BALANCE_URL)
            request = QNetworkRequest(url)
            request.setRawHeader(b"Authorization", f"Bearer {self.api_key}".encode("utf-8"))
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            
            reply = self.api_manager.get(request)
            reply.finished.connect(lambda: self._on_balance_api_reply(reply))
        except Exception as e:
            print(f"[DeepSeek] Greška pri dohvatanju balansa: {e}")
            self.status_label.setText("💰 Balans: ⚠️ Greška pri dohvatanju")
    
    def _on_balance_api_reply(self, reply):
        """Obradjuje odgovor od balance API-ja."""
        try:
            if reply.error() != QNetworkReply.NoError:
                err_msg = reply.errorString()
                status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
                
                # Ako imamo sačuvan balans, prikaži njega umesto greške
                if hasattr(self, '_balance_info') and self._balance_info:
                    bal = self._balance_info
                    self.status_label.setText(f"💰 Balans: {bal['total_balance']} {bal['currency']}")
                elif status_code == 402:
                    self._update_balance_display("0.00", "CNY", is_available=False)
                    self.status_label.setText("💰 Balans: 0.00 CNY (❌ Nema sredstava)")
                elif status_code == 401:
                    self.status_label.setText("💰 Balans: ❌ Nevažeći API ključ")
                elif status_code == 404:
                    self.status_label.setText("💰 Balans: ⚠️ API endpoint ne postoji")
                else:
                    detail = err_msg[:60]
                    print(f"[DeepSeek] Greška pri dohvatanju balansa: {err_msg} (HTTP {status_code})")
                    # Sačuvaj balans i prikaži staru vrednost
                    if hasattr(self, '_balance_info') and self._balance_info:
                        bal = self._balance_info
                        self.status_label.setText(f"💰 Balans: {bal['total_balance']} {bal['currency']}")
                
                try:
                    reply.deleteLater()
                except:
                    pass
                return
            
            data_bytes = reply.readAll().data()
            data = json.loads(data_bytes)
            
            is_available = data.get("is_available", False)
            balance_infos = data.get("balance_infos", [])
            
            total_balance = "0.00"
            currency = "CNY"
            
            if balance_infos and len(balance_infos) > 0:
                info = balance_infos[0]
                total_balance = info.get("total_balance", "0.00")
                currency = info.get("currency", "CNY")
            
            self._update_balance_display(total_balance, currency, is_available)
            
            if is_available:
                status_text = f"💰 Balans: {total_balance} {currency}"
            else:
                status_text = f"💰 Balans: {total_balance} {currency} (⚠️ Nedostupan)"
            
            self.status_label.setText(status_text)
            
            # Sačuvaj balans u fajl
            try:
                with open(get_data_file("balance_cache.txt"), "w", encoding="utf-8") as f:
                    f.write(json.dumps(self._balance_info))
            except:
                pass
            
        except Exception as e:
            print(f"[DeepSeek] Greška pri parsiranju balansa: {e}")
            # Pokaži sačuvani balans ako postoji
            if hasattr(self, '_balance_info') and self._balance_info:
                bal = self._balance_info
                self.status_label.setText(f"💰 Balans: {bal['total_balance']} {bal['currency']}")
        
        try:
            reply.deleteLater()
        except:
            pass
    
    def _update_balance_display(self, total_balance, currency, is_available=True):
        """Ažurira prikaz balansa u status bar-u (pored status_label)."""
        # Ovo je placeholder - balans se već prikazuje u status_label
        # Dodajemo i tooltip na status label
        if is_available:
            tooltip = f"💰 Preostali kredit: {total_balance} {currency}\n✅ Nalog je aktivan"
        else:
            tooltip = f"💰 Preostali kredit: {total_balance} {currency}\n❌ Nalog nije dostupan"
        
        self.status_label.setToolTip(tooltip)
        
        # Sačuvaj u atribut za kasnije korišćenje
        self._balance_info = {
            "total_balance": total_balance,
            "currency": currency,
            "is_available": is_available,
            "last_updated": datetime.now().strftime("%H:%M:%S")
        }

    # =========================================================================
    # 📡 API POZIV
    # =========================================================================
    def _call_api(self, messages_override=None):
        """Šalje zahtev DeepSeek API-ju sa tool definicijama."""
        log(f"🔵 _call_api() - model={self.current_model}, msgs={len(messages_override if messages_override else self.messages)}, override={'DA' if messages_override else 'NE'}")
        if not self.api_key:
            self._show_error_msg("API ključ nije podešen! Klikni na 🔑 API Key.")
            self._loop_active = False
            return

        # ⛔ Proveri STOP flag
        if self._stop_requested:
            self._loop_active = False
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            return

        # ⛔ Proveri limit tool callova
        if self._tool_call_count >= self._max_tool_calls:
            self._append_message("error", 
                f"⛔ <b>Prekoračen maksimalan broj poziva alata ({self._max_tool_calls}).</b> "
                f"AI je ušao u beskonačnu petlju. Pritisni 'New' da počneš iznova.")
            self._loop_active = False
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            self.status_label.setText(f"⛔ Previše tool callova ({self._tool_call_count})")
            return



        self._set_ui_enabled(False)

        if self._show_thinking:
            self._start_thinking_animation()
        else:
            self.status_label.setText("⏳ Razmišljam...")

        msgs = messages_override if messages_override else self.messages
        # ⚠️ Pre slanja proveri procenu tokena - ako je blizu limita, sažmi ODMAH
        # (ne čekaj API 400 grešku - to je stvaralo beskonačnu petlju!)
        est = count_context_tokens(msgs)
        if est > MAX_HISTORY_TOKENS:
            log(f"⚠️ _call_api: procena {est} tokena > limit {MAX_HISTORY_TOKENS} - sažimam pre slanja")
            self._summarize_history()
            msgs = self.messages
            est = count_context_tokens(msgs)
            log(f"⚠️ _call_api: posle sažimanja {est} tokena")
        # Validiraj i popravi poruke pre slanja API-ju
        msgs = validate_and_fix_messages(msgs)

        # 📡 Streaming isključen - radi stabilnije sa tool callovima
        use_streaming = False
        
        # 🧠 Odredi tool_choice i should_force_tools
        # ⚠️ VAŽNO: tool_choice: "required" koristimo SAMO za prvi poziv (kad nema messages_override).
        # Ako je messages_override postavljen, to znači da smo usred tool petlje i AI treba
        # da dobije šansu da odgovori tekstom. "required" u petlji tera AI da stalno zove alate!
        is_r1_model = "reasoner" in self.current_model or "r1" in self.current_model.lower()
        should_force_tools = False  # Default: ne forciramo alate
        
        # 🚀 DeepSeek API ne podržava "required" tool_choice
        # Uvek koristimo "auto" da izbegnemo grešku
        tool_choice = "auto"
        
        payload = {
            "model": self.current_model,
            "messages": msgs,
            "tools": TOOLS_DEFINITIONS,
            "tool_choice": tool_choice,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            # ⚠️ 8192 = maksimum za deepseek-chat. Sa 4096 AI često potroši
            # sav limit na razmišljanje (reasoning_content) pa vrati finish_reason="length"
            # sa praznim content-om i bez tool_calls.
            "max_tokens": 8192,
        }
        
        # 📡 Dodaj streaming ako je omogućen i nismo u tool petlji
        if use_streaming and tool_choice == "auto":
            payload["stream"] = True

        url = QUrl(DEEPSEEK_API_URL)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Authorization", f"Bearer {self.api_key}".encode("utf-8"))

        json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
        if use_streaming and tool_choice == "auto":
            # 📡 Streaming zahtev
            self._stream_was_active = True  # ⛔ Spriječi _on_api_reply da obradi ovaj reply
            self._stream_active = True
            self._stream_buffer = ""
            self._current_stream_content = ""
            self._stream_reply = self.manager.post(request, json_bytes)
            self._stream_reply.readyRead.connect(self._on_stream_data)
            self._stream_reply.finished.connect(self._on_stream_finished)
        else:
            # 📡 Običan zahtev (ili tool call)
            self._stream_active = False
            self._stream_reply = None
            self.manager.post(request, json_bytes)
        self._current_payload = payload

    # -------------------------------------------------------------------------
    # 📡 STREAMING OBRADA (SSE - Server-Sent Events)
    # -------------------------------------------------------------------------
    def _on_stream_data(self):
        """Obradjuje pristigle SSE chunkove tokom streaming-a."""
        if not self._stream_reply or not self._stream_active:
            return
        
        try:
            data = self._stream_reply.readAll().data().decode("utf-8", errors="replace")
        except:
            return
        
        self._stream_buffer += data
        
        # Parsiraj SSE: "data: {...}\n\n"
        while "\n" in self._stream_buffer:
            line, self._stream_buffer = self._stream_buffer.split("\n", 1)
            line = line.strip()
            
            if not line:
                continue
            if not line.startswith("data: "):
                continue
            
            json_str = line[6:]  # Skini "data: "
            if json_str == "[DONE]":
                continue
            
            try:
                chunk = json.loads(json_str)
            except:
                continue
            
            # Izvuci content delta
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content", "")
            
            if content:
                self._current_stream_content += content
                # Prikazi u chatu
                self._update_streaming_display()
                # Forsiraj UI da se ažurira i scroll dole
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                self.chat_display.verticalScrollBar().setValue(
                    self.chat_display.verticalScrollBar().maximum()
                )
    
    def _update_streaming_display(self):
        """Azurira prikaz streaming teksta - samo čuva content, ne prikazuje."""
        pass  # Ne prikazujemo dok se streaming ne završi
    
    def _on_stream_finished(self):
        """Kada se streaming zavrsi, obradi konacan odgovor."""
        if not self._stream_active:
            return
        
        self._stream_active = False
        self._stop_thinking_animation()
        
        # Prikazi ceo odgovor odjednom
        content = self._current_stream_content.strip()
        if content:
            self._append_message("assistant", self._escape_html(content))
            self.messages.append({"role": "assistant", "content": content})
            self._save_history()
            self._summarize_history()
            self.status_label.setText("✅ Odgovor primljen (streaming)")
        
        self._update_send_button(is_running=False)
        self._set_ui_enabled(True)
        self._loop_active = False
        self._stream_reply = None
    
    def _remove_streaming_cursor(self):
        """Uklanja trepćući cursor (▍) - nema ga, ali ostavljamo."""
        pass
    
    # -------------------------------------------------------------------------
    # ⏳ ANIMACIJA RAZMIŠLJANJA (peščani sat)
    # -------------------------------------------------------------------------
    def _start_thinking_animation(self):
        """Pokreće animaciju peščanog sata u status baru."""
        self._thinking_frames = 0
        self._thinking_timer = QTimer(self)
        self._thinking_timer.timeout.connect(self._update_thinking_animation)
        self._thinking_timer.start(800)  # Svake 0.8 sekundi
        self._update_thinking_animation()
    
    def _update_thinking_animation(self):
        """Ažurira animaciju - rotirajući peščani sat u status baru."""
        frames = ["⏳", "⌛"]
        frame = frames[self._thinking_frames % len(frames)]
        self._thinking_frames += 1
        
        # Prikaži u status baru umesto u chatu
        self.status_label.setText(f"{frame} DeepSeek razmišlja...")
    
    def _stop_thinking_animation(self):
        """Zaustavlja animaciju i vraća status bar u normalno stanje."""
        if self._thinking_timer:
            self._thinking_timer.stop()
            self._thinking_timer = None
        self._thinking_frames = 0
        # Vrati status bar u normalno stanje (ako nije već postavljen od strane odgovora)
        if self.status_label.text().startswith("⏳") or self.status_label.text().startswith("⌛"):
            self.status_label.setText(self._tr("status_ready"))

    # -------------------------------------------------------------------------
    # OBRADA ODGOVORA (function calling petlja)
    # -------------------------------------------------------------------------
    def _on_api_reply(self, reply: QNetworkReply):
        # ⛔ Ako je ovo bio streaming zahtev, preskoči - već ga je obradio _on_stream_finished
        if self._stream_was_active:
            self._stream_was_active = False
            return

        log("🟢 _on_api_reply() - stigao odgovor")
        # Ukloni "razmišljam..."
        self._remove_thinking_placeholder()

        if reply.error() != QNetworkReply.NoError:
            log(f"🔴 _on_api_reply() - GRESKA: {reply.errorString()[:100]}")
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            error_msg = reply.errorString()
            body = reply.readAll().data().decode("utf-8", errors="replace")
            
            # Probaj da izvučeš detaljnu poruku iz API odgovora
            error_detail = ""
            try:
                err_data = json.loads(body) if body else {}
                if "error" in err_data:
                    err = err_data["error"]
                    if isinstance(err, dict):
                        error_detail = err.get("message", "") or err.get("code", "") or str(err)
                    else:
                        error_detail = str(err)
            except:
                error_detail = body[:500] if body else ""

            # Mapa DeepSeek error kodova
            error_map = {
                400: "❌ Loš zahtev (Bad Request)",
                401: "❌ Nevažeći API ključ! Klikni na 🔑 API Key.",
                402: "💰 Nedovoljno sredstava na računu (Insufficient Balance)!",
                403: "🚫 Zabranjen pristup (Forbidden) - proveri IP dozvolu",
                404: "🔍 Model nije pronađen - proveri naziv modela u 🧠 Modeli",
                413: "📦 Zahtev je prevelik (Payload Too Large)",
                422: "⚠️ Neispravni parametri (Unprocessable Entity)",
                429: "⏳ Rate limit - sačekaj trenutak pre sledećeg zahteva",
                500: "🔧 Interna greška DeepSeek servera (Server Error)",
                503: "🔧 Servis trenutno nedostupan (Service Unavailable)",
            }

            error_text = error_map.get(status_code, f"❌ Greška ({status_code})")
            
            # Prikaži detalje ako postoje
            if error_detail:
                display_msg = f"{error_text}<br><span style='color: #ffaa44; font-size: 10px;'>{self._escape_html(error_detail[:300])}</span>"
            else:
                display_msg = f"{error_text}<br><span style='color: #888; font-size: 10px;'>{self._escape_html(str(error_msg))}</span>"
            
            self._append_message("error", display_msg)

            if status_code == 401:
                self._show_error_msg("Nevažeći API ključ! Klikni na 🔑 API Key.")
            elif status_code == 402:
                self._show_error_msg("Nedovoljno sredstava na DeepSeek računu!")
            elif status_code == 429:
                pass  # Već prikazano u chatu
            else:
                if "context length" in error_detail.lower() or "context" in error_detail.lower():
                    # 🛑 ZAUSTAVI BESKONAČNU PETLJU: ako sažimanje ne reši problem
                    # posle 3 pokušaja, prekini - ne zovi API u krug!
                    self._summarize_retry_count = getattr(self, "_summarize_retry_count", 0) + 1
                    if self._summarize_retry_count > 3:
                        log(f"🛑 Context limit petlja prekinuta nakon {self._summarize_retry_count} pokušaja!")
                        self._append_message("error",
                            f"⛔ <b>Context limit prekoračen i sažimanje ne pomaže</b> "
                            f"({self._summarize_retry_count} pokušaja). "
                            f"Fajlovi/poruke su preveliki. Pritisni 🗑️ New da počneš novi razgovor.")
                        self._show_error_msg("Context limit - sažimanje ne pomaže. Pritisni 'New' za novi razgovor.")
                        self.status_label.setText("⛔ Context limit - petlja prekinuta")
                        self._stop_thinking_animation()
                        self._update_send_button(is_running=False)
                        self._set_ui_enabled(True)
                        self._loop_active = False
                        self.input_field.setFocus()
                        return
                    
                    self._show_error_msg("Context limit prekoračen! Automatski sažimam history...")
                    # Automatski sažmi history i pokušaj ponovo
                    if self._summarize_history():
                        self.status_label.setText("🔄 History sažet - pokušavam ponovo...")
                        # Pokušaj ponovo sa sažetim historyjem
                        QTimer.singleShot(500, lambda: self._call_api(messages_override=self.messages))
                        return  # Ne prekidaj petlju
                else:
                    self._show_error_msg(f"API greška ({status_code})")

            self.status_label.setText(f"❌ Greška ({status_code})")
            self._stop_thinking_animation()
            reply.deleteLater()
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            self._loop_active = False
            self.input_field.setFocus()
            return

        # Uspesan odgovor
        response_bytes = reply.readAll().data()
        reply.deleteLater()

        try:
            data = json.loads(response_bytes)
        except json.JSONDecodeError as e:
            self._append_message("error", f"❌ Greška u parsiranju odgovora: {e}")
            self._append_message("error", f"Sirovi odgovor: {response_bytes.decode('utf-8', 'replace')[:500]}")
            self.status_label.setText("❌ Greška parsiranja")
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            self._loop_active = False
            return

        try:
            choice = data["choices"][0]
            message = choice["message"]
        except (KeyError, IndexError) as e:
            self._append_message("error", f"❌ Neočekivani format odgovora: {e}")
            self._append_message("error", f"Sadržaj: {json.dumps(data, indent=2)[:500]}")
            self.status_label.setText("❌ Greška formata")
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            self._loop_active = False
            return

        # Proveri da li ima tool_calls
        tool_calls = message.get("tool_calls")

        if tool_calls:
            # AI želi da pozove alatke
            self._handle_tool_calls(message, tool_calls)
        else:
            # AI daje tekstualni odgovor
            content = message.get("content")
            if content:
                self._append_message("assistant", self._escape_html(content))
                self.messages.append({"role": "assistant", "content": content})
                self._save_history()
                # 🔄 Sažmi history ako je prevelik
                self._summarize_history()
                self.status_label.setText("✅ Odgovor primljen")
                
                # 📝 Sačuvaj kontekst projekta (poslednja user poruka + odgovor)
                if self.project_path:
                    last_user = ""
                    for m in reversed(self.messages):
                        if m["role"] == "user":
                            last_user = m.get("content", "")
                            break
                    if last_user:
                        self._append_project_context(last_user, content)
            else:
                # 🔍 Detaljno dijagnostikuj prazan odgovor
                finish_reason = choice.get("finish_reason", "nepoznato")
                raw_msg = json.dumps(message, ensure_ascii=False) if message else "None"
                reasoning = (message.get("reasoning_content") or "") if isinstance(message, dict) else ""

                # 🎯 finish_reason == "length": AI je potrošio token limit na razmišljanje
                # pa nije stigao da vrati ni tekst ni poziv alata. Pokušaj ponovo
                # sa uputstvom da ODMAH odgovori bez dugog razmišljanja.
                if finish_reason == "length":
                    retry_count = getattr(self, "_retry_length_count", 0) + 1
                    self._retry_length_count = retry_count
                    if retry_count <= 2:
                        self._append_message("error",
                            f"⚠️ <b>Token limit potrošen na razmišljanje!</b> "
                            f"(pokušaj {retry_count}/2)<br>"
                            f"<span style='color: #888; font-size: 10px;'>AI je iskoristio svih "
                            f"8192 tokena na razmišljanje, pa nije stigao da odgovori. "
                            f"🔄 Pokušavam ponovo sa uputstvom da odmah odgovori...</span>")
                        self.status_label.setText("🔄 Retry (token limit)...")

                        # Pošalji AI-ju povratnu poruku da odmah odgovori bez dugog razmišljanja
                        self.messages.append({
                            "role": "user",
                            "content": (
                                "[SISTEM] Tvoj prethodni odgovor je prekinut jer si potrošio "
                                "maksimalan broj tokena na razmišljanje (reasoning_content). "
                                "Sada ODMAH daj konkretan odgovor ili pozovi odgovarajući alat. "
                                "NE piši duge analize i planove - samo uradi posao što kraće!"
                            )
                        })
                        # Ne diraj UI - _call_api će ponovo postaviti thinking animaciju.
                        # Petlja ostaje aktivna (ne postavljamo _loop_active = False).
                        QTimer.singleShot(300, self._call_api)
                        self._stop_thinking_animation()
                        return
                    else:
                        # Dva pokušaja nisu uspela - odustani
                        self._retry_length_count = 0
                        self._append_message("error",
                            "❌ <b>AI i dalje troši sav token limit na razmišljanje.</b> "
                            "Probaj da podeliš zahtev na manje delove ili prebaci na drugi model.")
                        self.status_label.setText("❌ Token limit (2 pokušaja)")
                else:
                    self._append_message("error", 
                        f"⚠️ AI nije vratio ni tekst ni poziv alata.\n"
                        f"🔍 finish_reason: {finish_reason}\n"
                        f"🔍 message: {raw_msg[:300]}")
                    self.status_label.setText(f"❌ Prazan odgovor (finish_reason={finish_reason})")

            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            self._loop_active = False
            self._stop_thinking_animation()
            
            # 💰 Osveži balans posle svake poruke
            QTimer.singleShot(500, self.fetch_user_balance)

    def _handle_tool_calls(self, message, tool_calls):
        """Obradjuje pozive alata od AI-ja."""
        # Zaustavi thinking animaciju - AI je počeo da radi
        self._stop_thinking_animation()
        
        # ⛔ Proveri STOP flag
        if self._stop_requested:
            self._loop_active = False
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            return

        # Broji tool callove
        self._tool_call_count += len(tool_calls)
        self.status_label.setText(f"🔧 Tool call #{self._tool_call_count}/{self._max_tool_calls}...")

        # ⛔ Ako je previše tool callova, prekini
        if self._tool_call_count >= self._max_tool_calls:
            self._append_message("error",
                f"⛔ <b>Previše tool callova ({self._tool_call_count})!</b> "
                f"Maksimum: {self._max_tool_calls}. Prekidam petlju.")
            self._loop_active = False
            self._update_send_button(is_running=False)
            self._set_ui_enabled(True)
            self.status_label.setText(f"⛔ Previše tool callova ({self._tool_call_count})")
            self._stop_thinking_animation()
            return

        # 🔄 Detekcija ponavljajućeg obrasca (petlje)
        # ⚠️ Loop zaštita se odnosi SAMO na operacije koje menjaju stanje:
        # create_file / edit_file / run_command (del/rm = brisanje).
        # Čitanje (read_file, list_files, search_text, read_log, get_issues)
        # se NE prati - AI mora slobodno da čita fajlove bez lažne petlje.
        WRITE_TOOLS = {"create_file", "edit_file", "run_command"}
        for tc in tool_calls:
            name = tc["function"]["name"]
            if name in WRITE_TOOLS:
                self._last_tool_names.append(name)
        # Čuvaj samo poslednjih 7
        if len(self._last_tool_names) > 7:
            self._last_tool_names = self._last_tool_names[-7:]
        
        # Proveri da li se isti pattern ponavlja (npr. create→del→create→del)
        # ALI: ne smatraj petljom ako su svi alati isti (npr. create×20 = normalno)
        # PATTERN_DETECT_LIMIT se setuje u ⚙️ Settings (0 = iskljuceno)
        # ⚠️ Koristimo self._tool_call_count (ukupan broj do sada) umesto
        # len(self._last_tool_names) koji je ograničen na 7
        if PATTERN_DETECT_LIMIT > 0 and self._tool_call_count >= PATTERN_DETECT_LIMIT:
            last6 = self._last_tool_names[-6:]
            # Ako su svih 6 isti alati (npr. create_file × 6) - to NIJE petlja
            if len(set(last6)) > 1:
                first3 = last6[:3]
                last3 = last6[3:]
                if first3 == last3:
                    # Isti pattern od 3 alata se ponovio!
                    self._append_message("error",
                        f"🔄 <b>AI je ušao u petlju!</b> Detektovan ponavljajući pattern: "
                        f"{' → '.join(first3)} → {' → '.join(last3)}. Petlja prekinuta.")
                    self._loop_active = False
                    self._update_send_button(is_running=False)
                    self._set_ui_enabled(True)
                    self.status_label.setText("🔄 Petlja detektovana - STOP")
                    # Dodaj u istoriju da AI zna da je prekinut
                    self.messages.append({
                        "role": "assistant",
                        "content": "[Petlja je detektovana i prekinuta. Završi sa odgovorom, nemoj ponovo pozivati alate.]"
                    })
                    return

        # Dodaj asistent poruku u istoriju
        msg_copy = dict(message)
        msg_copy.pop("tool_calls", None)  # ne saljemo tool_calls nazad u sledecem zahtevu
        assistant_msg = {
            "role": "assistant",
            "content": message.get("content"),
            "tool_calls": tool_calls
        }
        self.messages.append(assistant_msg)

        # Izvrsi svaki alat
        tool_messages = []
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            func_args = tc["function"]["arguments"]
            tool_call_id = tc["id"]

            # 🗑️ Detekcija: fajl je obrisan → zapamti ga
            # ⚠️ Ograniči veličinu seta na 20 da ne raste beskonačno
            if len(self._recreated_files) > 20:
                self._recreated_files.clear()
            if func_name == "run_command":
                try:
                    args_dict = json.loads(func_args) if isinstance(func_args, str) else func_args
                    cmd = args_dict.get("command", "")
                    if cmd.startswith("del ") or cmd.startswith("rm "):
                        # Izdvoji ime fajla iz komande "del fajl.txt fajl.txt.bak"
                        parts = cmd.replace("del ", "").replace("rm ", "").split()
                        for p in parts:
                            if p.endswith(".bak"):
                                continue
                            self._recreated_files.add(p)
                except:
                    pass

            # 🗑️ Detekcija: fajl se kreira, a već je obrisan u ovoj petlji
            if func_name == "create_file":
                try:
                    args_dict = json.loads(func_args) if isinstance(func_args, str) else func_args
                    filepath = args_dict.get("filepath", "")
                    if filepath in self._recreated_files:
                        # ⛔ Kreira se fajl koji je već obrisan - petlja!
                        self._append_message("error",
                            f"🔄 <b>AI kreira fajl koji je upravo obrisao!</b> "
                            f"Fajl '{filepath}' je obrisan pa se ponovo kreira. "
                            f"Petlja prekinuta.")
                        self._loop_active = False
                        self._update_send_button(is_running=False)
                        self._set_ui_enabled(True)
                        self.status_label.setText("🔄 Create-Del petlja - STOP")
                        # ⚠️ VAŽNO: Dodaj sve do sada izvršene tool rezultate
                        # + fallback za preostale, da API ne vrati 400
                        # (assistant sa tool_calls MORA imati sve tool odgovore!)
                        self.messages.extend(tool_messages)
                        done_ids = {m["tool_call_id"] for m in tool_messages}
                        for tc_rest in tool_calls:
                            if tc_rest.get("id") not in done_ids:
                                self.messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc_rest["id"],
                                    "content": "[Tool call interrupted - create/delete loop detected. Continue without it.]"
                                })
                        self.messages.append({
                            "role": "assistant",
                            "content": "[Create-Delete petlja detektovana. Prekini sa alatima i daj odgovor korisniku.]"
                        })
                        return
                except:
                    pass

            # Prikazi sta AI radi
            args_preview = func_args[:200] if len(func_args) > 200 else func_args
            self._append_message("tool_call",
                f"🔧 <b>{func_name}</b>({self._escape_html(args_preview)})")

            # Izvrsi
            executor = ToolExecutor(self.project_path, self)
            log(f"🔧 TOOL: {func_name}({func_args[:80] if func_args else 'None'})")
            t0 = datetime.now()
            result = executor.dispatch(func_name, func_args)
            dt_ms = (datetime.now() - t0).total_seconds() * 1000
            log(f"🔧 TOOL KRAJ: {func_name} ({dt_ms:.0f} ms, rezultat {len(result) if result else 0} chars)")
            # ⚠️ Zaštita: dispatch uvek mora vratiti string (None = nema rezultata)
            if result is None:
                result = "(no output)"

            # Prikazi notifikaciju u chatu za uspešno kreiranje/izmenu fajla
            if func_name == "create_file" and "✅ File created successfully" in result:
                filepath = json.loads(func_args).get("filepath", "?")
                self._append_system_message(f"📄 <b>Kreiran fajl:</b> {filepath}")
                # 📝 Sačuvaj u kontekst projekta - kreiranje fajla je BITNO!
                self._save_project_context(
                    f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] 🔧 create_file: {filepath}"
                )
            elif func_name == "edit_file" and "✅ File edited successfully" in result:
                filepath = json.loads(func_args).get("filepath", "?")
                self._append_system_message(f"✏️ <b>Izmenjen fajl:</b> {filepath}")
                # 📝 Sačuvaj u kontekst projekta - izmena fajla je BITNA!
                self._save_project_context(
                    f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] ✏️ edit_file: {filepath}"
                )
            elif func_name == "run_command" and "✅ Command completed successfully" in result:
                try:
                    cmd = json.loads(func_args).get("command", "")[:120]
                    # 📝 Sačuvaj uspešne komande (build, git, itd.) - BITNO za kontekst!
                    self._save_project_context(
                        f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] 💻 run_command: {cmd}"
                    )
                except:
                    pass

            if len(result) > 1000:
                result_preview = result[:1000] + f"\n... ({len(result)} chars total)"
            else:
                result_preview = result

            self._append_message("tool_result",
                f"📋 Rezultat <b>{func_name}</b>:<br><pre style='font-size:10px;'>{self._escape_html(result_preview)}</pre>")

            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result
            })

        # Dodaj tool rezultate u istoriju
        self.messages.extend(tool_messages)

        # 🔄 Sažmi history ako su tool rezultati preveliki
        # ⚠️ VAŽNO: ne sažimamo TOKOM tool petlje jer bi to obrisalo tool poruke
        # i izazvalo 400 grešku (assistant + tool_calls bez tool rezultata)
        # Samo proveravamo da li je prekoračen MAX_CONTEXT_TOKENS ali NE sažimamo
        total_tokens = count_context_tokens(self.messages)
        if total_tokens > MAX_CONTEXT_TOKENS:
            self._save_history()
            self._append_system_message(
                f"⚠️ <b>Context limit blizu:</b> {total_tokens:,} tokena. "
                f"Sažimanje će se desiti posle AI odgovora."
            )

        # Nastavi petlju - pozovi API ponovo sa rezultatima
        self._call_api(messages_override=self.messages)

    # -------------------------------------------------------------------------
    # POTVRDE ZA FILE OPERACIJE
    # -------------------------------------------------------------------------
    def _confirm_create_file(self, filepath, content):
        """Traži korisničku potvrdu za kreiranje fajla."""
        if self.auto_apply:
            # ⚡ Auto-apply mod - broji fajlove
            self._files_created_in_session += 1
            
            # 📊 Ažuriraj prikaz brojača
            remaining = self._max_files_per_session - self._files_created_in_session
            self.status_label.setText(f"⚡ Auto-apply: {self._files_created_in_session}/{self._max_files_per_session}")
            self.btn_auto_apply.setToolTip(f"Auto-apply: {self._files_created_in_session} fajlova kreirano, još {remaining}")
            
            # ⛔ Ako je prekoračen limit, isključi auto-apply
            if self._files_created_in_session >= self._max_files_per_session:
                self.auto_apply = False
                self.btn_auto_apply.setChecked(False)
                self.status_label.setText(f"⛔ Auto-apply isključen - limit ({self._max_files_per_session}) dostignut")
                self.btn_auto_apply.setToolTip("Auto-apply je automatski isključen (limit dostignut)")
                self._append_system_message(
                    f"⛔ <b>Auto-apply automatski isključen!</b> "
                    f"Kreirano je {self._files_created_in_session} fajlova u ovoj sesiji. "
                    f"Dalje kreiranje zahteva potvrdu."
                )
                # Onda traži potvrdu za ovaj fajl
                return self._ask_confirm_create_file(filepath, content)
            
            return True  # Auto-apply radi
        return self._ask_confirm_create_file(filepath, content)

    def _ask_confirm_create_file(self, filepath, content):
        """Prikazuje dijalog za potvrdu kreiranja fajla."""
        preview = content[:500] + ("..." if len(content) > 500 else "")
        msg = QMessageBox(self)
        msg.setWindowTitle("📄 Kreiranje fajla")
        msg.setText(f"Da li želiš da kreiram novi fajl?\n\n<b>Fajl:</b> {filepath}\n<b>Veličina:</b> {len(content)} karaktera")
        msg.setDetailedText(f"Sadržaj:\n{preview}")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.button(QMessageBox.Yes).setText("✅ Kreiraj")
        msg.button(QMessageBox.No).setText("❌ Odustani")
        return msg.exec_() == QMessageBox.Yes

    def _confirm_edit_file(self, filepath, old_text, new_text):
        """Prikazuje diff dijalog i traži potvrdu."""
        if self.auto_apply:
            # ⚡ Auto-apply mod - preskoči pitanje
            return True
        dlg = DiffDialog(
            "✏️ Potvrda izmene fajla",
            filepath,
            old_text,
            new_text,
            self
        )
        return dlg.exec_() == QDialog.Accepted

    # -------------------------------------------------------------------------
    # POMOCNE FUNKCIJE
    # -------------------------------------------------------------------------
    def _remove_thinking_placeholder(self):
        """Uklanja poslednji 'razmišljam...' placeholder iz prikaza."""
        doc = self.chat_display.document()
        block = doc.lastBlock()
        block_text = block.text()
        if "razmišljam" in block_text or (block.blockNumber() > 0 and
            doc.findBlockByNumber(block.blockNumber() - 1).text().find("razmišljam") >= 0):
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
            # Ukloni i prethodni block ako je potrebno
            doc = self.chat_display.document()
            block2 = doc.lastBlock()
            if "razmišljam" in block2.text():
                cursor2 = self.chat_display.textCursor()
                cursor2.movePosition(QTextCursor.End)
                cursor2.select(QTextCursor.BlockUnderCursor)
                cursor2.removeSelectedText()
                cursor2.deleteChar()

    def _set_ui_enabled(self, enabled):
        self.input_field.setEnabled(enabled)
        # send_btn NE diramo - on je ujedno i STOP dugme, mora da radi uvek!
        self.btn_settings.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        self.btn_project.setEnabled(enabled)
        self.btn_history.setEnabled(enabled)
        self.btn_auto_apply.setEnabled(enabled)
        self.btn_about.setEnabled(enabled)
        self.btn_models.setEnabled(enabled)
        self.btn_settings_config.setEnabled(enabled)
        # ⭐️ Vrati fokus na input polje kad UI postane omogućen
        if enabled:
            self.input_field.setFocus()
            # Ako nešto ukrade fokus posle, vrati posle kratke pauze
            QTimer.singleShot(100, self.input_field.setFocus)

    def _show_error_msg(self, text):
        QMessageBox.warning(self, "Greška", text)
        self.status_label.setText("❌ " + text.split("\n")[0])

    def _clear_chat(self):
        """Briše razgovor, zadržava system prompt i history fajl."""
        # Dodaj SAŽETAK konteksta projekta u system prompt ako postoji
        system_content = SYSTEM_PROMPT
        if self.project_context:
            ctx_summary = self._get_project_context_summary()
            if ctx_summary:
                system_content += f"\n\n{ctx_summary}\n\nNastavi rad na projektu na osnovu gore navedenog konteksta."
        
        self.messages = [{"role": "system", "content": system_content}]
        self.chat_display.clear()
        self._show_welcome()
        self.status_label.setText("🗑️ Razgovor obrisan (history sačuvan)")
        self._loop_active = False
        self._stop_requested = False
        self._tool_call_count = 0
        self._last_tool_names = []
        self._recreated_files = set()
        self._files_created_in_session = 0  # Reset brojača fajlova
        self._current_session_id = None  # 📜 Nova sesija - resetuj ID da se napravi nova
        self._update_send_button(is_running=False)


# =============================================================================
# POKRETANJE
# =============================================================================
# ⚠️ Glavna ulazna tačka je main.py (splash screen + tamna paleta + sve).
# Ovo omogućava i staru komandu:  python deepseek_chatbot.py
if __name__ == "__main__":
    import main
    main.main()
