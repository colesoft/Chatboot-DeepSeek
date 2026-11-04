# -*- coding: utf-8 -*-
"""dialogs.py - DialogsMixin (API kljuc, About, Podesavanja, Modeli)."""
import json
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QInputDialog, QPushButton, QMessageBox, QTextEdit, QTabWidget, QFormLayout, QComboBox, QFrame, QWidget, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, QUrl, QTimer, QEventLoop
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from ..config import (get_data_file, load_settings, save_settings, load_models_config, save_models_config, MAX_TOOL_CALLS, MAX_FILES_PER_SESSION, MAX_HISTORY_TOKENS, MAX_CONTEXT_TOKENS, MAX_SESSION_HISTORY, KEEP_MESSAGES_ON_SUMMARY, PATTERN_DETECT_LIMIT, STREAMING_ENABLED, TEMPERATURE, TOP_P, DEEPSEEK_MODELS, DEFAULT_MODEL, DEEPSEEK_LIST_MODELS_URL, FALLBACK_MODELS)
from ..i18n import ABOUT_TEXT
from ..utils import get_deepseek_icon
from ..logger import log


class DialogsMixin:
    """API kljuc, About, Podesavanja, Modeli dijalozi."""

    def _ask_for_api_key(self):
        if not self.isVisible():
            # Sačekaj da prozor bude vidljiv pre prikaza dijaloga
            QTimer.singleShot(200, self._ask_for_api_key)
            return
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("🔑 DeepSeek API Ključ")
            dlg.setWindowIcon(get_deepseek_icon())
            dlg.setFixedSize(520, 430)
            dlg.setStyleSheet("QDialog { background: #1a1a2e; }")

            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(20, 18, 20, 16)
            layout.setSpacing(10)

            # ---- Naslov ----
            title = QLabel("🔑 <b>DeepSeek API Ključ</b>")
            title.setStyleSheet("color: #e94560; font-size: 15px; background: transparent;")
            layout.addWidget(title)

            # ---- Uputstvo ----
            info = QLabel(
                '<div style="color: #e0e0e0; font-size: 12px; line-height: 1.5;">'
                '<span style="color: #8899bb; font-weight: bold;">Kako do DeepSeek API ključa:</span><br>'
                '1. Idi na <span style="color: #4fc3f7;">platform.deepseek.com</span><br>'
                '2. Registruj se (<span style="color: #66bb6a; font-weight: bold;">besplatno</span>)<br>'
                '3. Napravi API ključ<br>'
                '4. Dobijaš <span style="color: #ffd54f; font-weight: bold;">5.000.000 besplatnih tokena</span> za test<br>'
                '5. Unesi ključ ovde i počni sa radom!<br><br>'
                '<span style="color: #8899bb;">Vaš chatbot je optimizovan isključivo za DeepSeek.</span>'
                '</div>'
            )
            info.setTextFormat(Qt.RichText)
            info.setWordWrap(True)
            info.setStyleSheet("background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 12px;")
            layout.addWidget(info)

            # ---- Dugme za registraciju (otvara browser) ----
            btn_register = QPushButton("🌐 Registruj se na platform.deepseek.com")
            btn_register.setStyleSheet(
                "QPushButton { background: #0f3460; color: #4fc3f7; border: 1px solid #4fc3f7; "
                "border-radius: 6px; padding: 10px; font-size: 12px; font-weight: bold; }"
                "QPushButton:hover { background: #1a4a7a; color: #ffffff; }"
            )
            btn_register.setCursor(Qt.PointingHandCursor)
            btn_register.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl("https://platform.deepseek.com"))
            )
            layout.addWidget(btn_register)

            # ---- Unos ključa ----
            lbl_key = QLabel("🔑 Unesi svoj DeepSeek API ključ:")
            lbl_key.setStyleSheet("color: #ccc; font-size: 12px; background: transparent;")
            layout.addWidget(lbl_key)

            self._api_key_edit = QLineEdit()
            self._api_key_edit.setEchoMode(QLineEdit.Password)
            self._api_key_edit.setPlaceholderText("sk-...")
            if self.api_key:
                self._api_key_edit.setText(self.api_key)
            self._api_key_edit.setStyleSheet(
                "QLineEdit { background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; "
                "border-radius: 6px; padding: 8px; font-size: 13px; }"
                "QLineEdit:focus { border: 1px solid #e94560; }"
            )
            layout.addWidget(self._api_key_edit)

            # ---- Dugmad OK / Cancel ----
            bf = QHBoxLayout()
            bf.addStretch()
            btn_cancel = QPushButton("Odustani")
            btn_cancel.setStyleSheet(
                "QPushButton { background: transparent; color: #888; border: 1px solid #444; "
                "border-radius: 6px; padding: 8px 20px; font-size: 12px; }"
                "QPushButton:hover { color: #fff; border-color: #888; }"
            )
            btn_cancel.clicked.connect(dlg.reject)
            bf.addWidget(btn_cancel)
            btn_ok = QPushButton("✅ Sačuvaj ključ")
            btn_ok.setStyleSheet(
                "QPushButton { background: #e94560; color: white; border: none; border-radius: 6px; "
                "padding: 8px 20px; font-size: 12px; font-weight: bold; }"
                "QPushButton:hover { background: #ff6b6b; }"
            )
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            bf.addWidget(btn_ok)
            layout.addLayout(bf)

            QTimer.singleShot(10, lambda: self._center_dialog(dlg, 520, 430))
            if dlg.exec_() == QDialog.Accepted:
                key = self._api_key_edit.text().strip()
                if key:
                    self.api_key = key
                    with open(get_data_file("api_key.txt"), "w") as f:
                        f.write(self.api_key)
                    self.status_label.setText(self._tr("status_saved"))
                    # 🔄 Učitaj modele i balans nakon unosa ključa
                    QTimer.singleShot(500, self.fetch_models_from_api)
                    QTimer.singleShot(1000, self.fetch_user_balance)
                else:
                    self._show_error_msg(self._tr("key_empty"))
        except Exception as e:
            print(f"[DeepSeek] Greška pri unosu API ključa: {e}")

    def _show_about(self):
        """Prikazuje About dijalog sa tri jezika."""
        dlg = QDialog()  # Bez parenta - nezavisan prozor!
        dlg.setWindowTitle("💖 O programu / About / 关于")
        dlg.setWindowIcon(get_deepseek_icon())
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        dlg.setFixedSize(550, 520)

        # ---- Custom Title Bar ----
        tb = QFrame()
        tb.setFixedHeight(34)
        tb.setStyleSheet("QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f3460, stop:1 #1a4a7a); }")
        tbh = QHBoxLayout(tb)
        tbh.setContentsMargins(8, 0, 0, 0)
        tbh.setSpacing(4)
        ic = QLabel()
        pix = get_deepseek_icon().pixmap(16, 16)
        ic.setPixmap(pix)
        ic.setFixedSize(16, 16)
        ic.setStyleSheet("background: transparent;")
        tbh.addWidget(ic)
        tt = QLabel("💖 About / O programu / 关于")
        tt.setStyleSheet("color: #fff; font-size: 11px; font-weight: 500; background: transparent;")
        tbh.addWidget(tt)
        tbh.addStretch()
        bc = "QPushButton { background: transparent; color: #ffffffcc; border: none; border-radius: 0px; padding: 2px 10px; font-size: 12px; min-width: 30px; min-height: 24px; } QPushButton:hover { background: #e94560; color: white; }"
        cb = QPushButton("✕")
        cb.setStyleSheet(bc)
        cb.clicked.connect(dlg.accept)
        tbh.addWidget(cb)
        tb.mousePressEvent = lambda e: setattr(dlg, '_dp', e.globalPos() - dlg.frameGeometry().topLeft()) if e.button() == Qt.LeftButton else None
        tb.mouseMoveEvent = lambda e: dlg.move(e.globalPos() - dlg._dp) if hasattr(dlg, '_dp') and e.buttons() == Qt.LeftButton else None

        # ---- Sadržaj ----
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(tb)

        content = QWidget()
        content.setStyleSheet("background: #1a1a2e;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(8)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #0f3460; background: #16213e; border-radius: 8px; } QTabBar::tab { background: #1a1a2e; color: #888; padding: 8px 20px; font-size: 12px; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; } QTabBar::tab:selected { background: #16213e; color: #e94560; font-weight: bold; border-bottom: 2px solid #e94560; } QTabBar::tab:hover { color: #e0e0e0; }")
        for lang_key in ["srpski", "english", "中文"]:
            t = QTextEdit()
            t.setReadOnly(True)
            t.setHtml(ABOUT_TEXT[lang_key])
            t.setStyleSheet("QTextEdit { background: #16213e; color: #e0e0e0; border: none; padding: 12px; font-size: 13px; }")
            tabs.addTab(t, lang_key)
        cl.addWidget(tabs)

        fl = QLabel('<div style="text-align: center; padding: 8px;"><span style="color: #e94560;">❤️</span> <span style="color: #888; font-size: 11px;">Cole_Soft · DeepSeek · 中国 · 深圳 · 世界</span></div>')
        fl.setTextFormat(Qt.RichText)
        fl.setStyleSheet("background: transparent;")
        cl.addWidget(fl)

        bf = QHBoxLayout()
        bf.addStretch()
        cb2 = QPushButton("✕ Zatvori / Close / 关闭")
        cb2.setStyleSheet("QPushButton { background: #e94560; color: white; border: none; border-radius: 6px; padding: 8px 24px; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #ff6b6b; }")
        cb2.clicked.connect(dlg.accept)
        bf.addWidget(cb2)
        cl.addLayout(bf)

        layout.addWidget(content)

        # Centriraj POSLE show-a (QTimer osigurava da geometrija postoji)
        QTimer.singleShot(10, lambda: self._center_dialog(dlg, 550, 520))
        dlg.exec_()

    def _center_dialog(self, dlg, w, h):
        """Centrira frameless dijalog na SREDINU EKRANA."""
        try:
            screen = QApplication.primaryScreen().availableGeometry()
            cx = screen.center().x() - w // 2
            cy = max(screen.y() + 50, screen.center().y() - h // 2)
            dlg.move(cx, cy)
        except:
            pass

    # -------------------------------------------------------------------------
    # ⚙️ SETTINGS DIJALOG
    # -------------------------------------------------------------------------
    def _show_settings_dialog(self):
        """Prikazuje dijalog za podesavanja."""
        settings = load_settings()
        
        dlg = QDialog(self)
        dlg.setWindowTitle("⚙️ Podešavanja")
        dlg.setWindowIcon(get_deepseek_icon())
        dlg.setFixedSize(520, 900)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        # Naslov
        title = QLabel("<b>⚙️ Podešavanja aplikacije</b>")
        title.setStyleSheet("color: #e94560; font-size: 14px;")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(8)
        
        # Max tool calls
        self._settings_tool_calls = QComboBox()
        for val in [20, 30, 50, 75, 100, 150, 200, 500, 1000]:
            self._settings_tool_calls.addItem(str(val), val)
        idx = self._settings_tool_calls.findData(settings["max_tool_calls"])
        if idx >= 0:
            self._settings_tool_calls.setCurrentIndex(idx)
        self._settings_tool_calls.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Max alata po poruci:")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Koliko alata (read, create, edit...) AI sme da pozove pre nego što se prinudno zaustavi")
        form.addRow(lbl, self._settings_tool_calls)

        # 🧠 reasoning_effort (thinking mode)
        self._settings_effort = QComboBox()
        for val, text in [("auto", "Auto (default iz /models)"),
                          ("low", "Low - brzo, malo razmišljanja"),
                          ("high", "High - detaljnije"),
                          ("max", "Max - najdublje (sporo)"),
                          ("none", "Off - bez razmišljanja")]:
            self._settings_effort.addItem(text, val)
        idx = self._settings_effort.findData(settings.get("reasoning_effort", "auto"))
        if idx >= 0:
            self._settings_effort.setCurrentIndex(idx)
        self._settings_effort.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("🧠 Reasoning effort:")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Koliko duboko model razmišlja pre odgovora (reasoning_effort).\n"
                       "Šalje se samo modelima koji to podržavaju (vidi /models).")
        form.addRow(lbl, self._settings_effort)

        # 👁️ vision_detail
        self._settings_vision_detail = QComboBox()
        for val, text in [("auto", "Auto"), ("low", "Low (manje tokena)"),
                          ("high", "High (detaljnije)")]:
            self._settings_vision_detail.addItem(text, val)
        idx = self._settings_vision_detail.findData(settings.get("vision_detail", "auto"))
        if idx >= 0:
            self._settings_vision_detail.setCurrentIndex(idx)
        self._settings_vision_detail.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("👁️ Detalj slike:")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Koliko detaljno se analizira priložena slika (image_url.detail)")
        form.addRow(lbl, self._settings_vision_detail)

        # 🌐 Web alati
        self._settings_web_search = QCheckBox("Dozvoli web_search (pretraga)")
        self._settings_web_search.setChecked(bool(settings.get("web_search_enabled", True)))
        self._settings_web_search.setStyleSheet("color: #ccc;")
        self._settings_web_fetch = QCheckBox("Dozvoli web_fetch (čitanje stranica)")
        self._settings_web_fetch.setChecked(bool(settings.get("web_fetch_enabled", True)))
        self._settings_web_fetch.setStyleSheet("color: #ccc;")
        form.addRow(QLabel("🌐 Web alati:"), self._settings_web_search)
        form.addRow(QLabel(""), self._settings_web_fetch)
        
        # Max files auto-apply
        self._settings_max_files = QComboBox()
        for val in [5, 10, 15, 20, 30, 50, 100, 200, 500, 1000, 5000, 10000]:
            self._settings_max_files.addItem(str(val), val)
        idx = self._settings_max_files.findData(settings["max_files_per_session"])
        if idx >= 0:
            self._settings_max_files.setCurrentIndex(idx)
        self._settings_max_files.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Max fajlova (auto-apply):")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Kad je auto-apply uključen, posle ovog broja kreiranih fajlova se sam isključuje")
        form.addRow(lbl, self._settings_max_files)
        
        # History tokens before compression
        self._settings_history_tokens = QComboBox()
        for val in [1000, 2000, 5000, 8000, 10000, 20000, 50000]:
            label = f"{val:,}" if val >= 1000 else str(val)
            self._settings_history_tokens.addItem(label, val)
        idx = self._settings_history_tokens.findData(settings["max_history_tokens"])
        if idx >= 0:
            self._settings_history_tokens.setCurrentIndex(idx)
        self._settings_history_tokens.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Tokeni pre kompresije:")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Kada broj tokena u porukama (user/assistant) predje ovu vrednost, starije poruke se kompresuju u sazetak. Manje = cesce sazimanje, vise = duza istorija")
        form.addRow(lbl, self._settings_history_tokens)
        
        # Max context tokens
        self._settings_context_tokens = QComboBox()
        for val in [100000, 200000, 500000, 800000, 900000, 1000000]:
            label = f"{val:,}"
            self._settings_context_tokens.addItem(label, val)
        idx = self._settings_context_tokens.findData(settings["max_context_tokens"])
        if idx >= 0:
            self._settings_context_tokens.setCurrentIndex(idx)
        self._settings_context_tokens.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Maks context (API limit):")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Apsolutni maksimum tokena pre nego sto se istorija obavezno sazme. DeepSeek limit je ~1M tokena")
        form.addRow(lbl, self._settings_context_tokens)
        
        # Messages to keep on summary
        self._settings_keep_msgs = QComboBox()
        for val in [5, 10, 15, 20, 30]:
            self._settings_keep_msgs.addItem(str(val), val)
        idx = self._settings_keep_msgs.findData(settings["keep_messages_on_summary"])
        if idx >= 0:
            self._settings_keep_msgs.setCurrentIndex(idx)
        self._settings_keep_msgs.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Poruka posle kompresije:")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Koliko najnovijih poruka (user+assistant) sacuvati posle sazimanja istorije")
        form.addRow(lbl, self._settings_keep_msgs)
        
        # Max sessions in history
        self._settings_max_sessions = QComboBox()
        for val in [10, 20, 30, 50, 100]:
            self._settings_max_sessions.addItem(str(val), val)
        idx = self._settings_max_sessions.findData(settings["max_session_history"])
        if idx >= 0:
            self._settings_max_sessions.setCurrentIndex(idx)
        self._settings_max_sessions.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Max sesija u istoriji:")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Koliko sesija (razgovora) cuvati u history fajlu pre nego sto se najstarije obrisu")
        form.addRow(lbl, self._settings_max_sessions)

        # Pattern detection limit
        self._settings_pattern = QComboBox()
        # Ponudimo opcije: 0=iskljuceno, 20, 30, 50, 100, 200, 500, 1000, 5000, 10000
        pattern_options = [("Isključeno (0)", 0), ("20", 20), ("30", 30), ("50", 50), ("100", 100),
                           ("200", 200), ("500", 500), ("1000", 1000), ("5000", 5000), ("10000", 10000)]
        for label, val in pattern_options:
            self._settings_pattern.addItem(label, val)
        idx = self._settings_pattern.findData(settings["pattern_detect_limit"])
        if idx >= 0:
            self._settings_pattern.setCurrentIndex(idx)
        self._settings_pattern.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Pattern detekcija (petlja):")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Posle koliko tool callova da se aktivira pattern detekcija. Ako se isti 3 alata ponove, petlja se prekida. 0 = iskljuceno")
        form.addRow(lbl, self._settings_pattern)

        # Streaming toggle
        self._settings_streaming = QComboBox()
        self._settings_streaming.addItem("✅ Uključeno", True)
        self._settings_streaming.addItem("❌ Isključeno", False)
        idx = 0 if settings.get("streaming", True) else 1
        self._settings_streaming.setCurrentIndex(idx)
        self._settings_streaming.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Streaming (reč po reč):")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("AI odgovara u realnom vremenu umesto da čeka ceo odgovor. Bolji osećaj, ali ne radi sa tool call-ovima.")
        form.addRow(lbl, self._settings_streaming)

        # Temperature
        self._settings_temp = QComboBox()
        for val in [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0, 1.3, 1.5, 2.0]:
            self._settings_temp.addItem(f"{val:.1f}", val)
        idx = self._settings_temp.findData(settings.get("temperature", 0.3))
        if idx >= 0:
            self._settings_temp.setCurrentIndex(idx)
        self._settings_temp.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Temperature (kreativnost):")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Više = kreativniji odgovori, manje = precizniji. Preporuka: 0.3 za kod, 0.7 za opšte razgovore")
        form.addRow(lbl, self._settings_temp)

        # Top P
        self._settings_top_p = QComboBox()
        for val in [0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]:
            self._settings_top_p.addItem(f"{val:.2f}", val)
        idx = self._settings_top_p.findData(settings.get("top_p", 0.9))
        if idx >= 0:
            self._settings_top_p.setCurrentIndex(idx)
        self._settings_top_p.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 4px 8px;")
        lbl = QLabel("Top P (raznolikost):")
        lbl.setStyleSheet("color: #ccc;")
        lbl.setToolTip("Kontroliše raznolikost reči. 0.9 = dobra ravnoteža, 1.0 = maksimalna raznolikost")
        form.addRow(lbl, self._settings_top_p)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Info
        info = QLabel('<span style="color: #888; font-size: 10px;">Promene se primenjuju odmah i čuvaju u settings.json fajlu.</span>')
        layout.addWidget(info)
        
        # Dugmad
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Sačuvaj")
        save_btn.setStyleSheet("QPushButton { background: #e94560; color: white; font-weight: bold; border-radius: 6px; padding: 8px 24px; }")
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✕ Odustani")
        cancel_btn.clicked.connect(dlg.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Click save
        def _save_settings():
            nonlocal settings
            settings["max_tool_calls"] = self._settings_tool_calls.currentData()
            settings["max_files_per_session"] = self._settings_max_files.currentData()
            settings["max_history_tokens"] = self._settings_history_tokens.currentData()
            settings["max_context_tokens"] = self._settings_context_tokens.currentData()
            settings["keep_messages_on_summary"] = self._settings_keep_msgs.currentData()
            settings["max_session_history"] = self._settings_max_sessions.currentData()
            settings["pattern_detect_limit"] = self._settings_pattern.currentData()
            settings["streaming"] = self._settings_streaming.currentData()
            settings["temperature"] = self._settings_temp.currentData()
            settings["top_p"] = self._settings_top_p.currentData()
            # 🧠 / 👁️ / 🌐 novi model parametri
            settings["reasoning_effort"] = self._settings_effort.currentData()
            settings["vision_detail"] = self._settings_vision_detail.currentData()
            settings["web_search_enabled"] = self._settings_web_search.isChecked()
            settings["web_fetch_enabled"] = self._settings_web_fetch.isChecked()

            save_settings(settings)

            # 🧠 primeni reasoning_effort odmah (bez restarta)
            self.reasoning_effort = settings["reasoning_effort"]

            # 🌐 osveži listu web alata prema novim toggle-ima
            try:
                from ..tools import refresh_web_tools
                names = refresh_web_tools()
                log(f"🌐 Aktivni alati posle podešavanja: {names}")
            except Exception as e:
                log(f"⚠️ refresh_web_tools: {e}")
            
            # Azuriraj globalne promenljive
            global MAX_TOOL_CALLS, MAX_FILES_PER_SESSION, MAX_HISTORY_TOKENS, MAX_CONTEXT_TOKENS, KEEP_MESSAGES_ON_SUMMARY, MAX_SESSION_HISTORY, PATTERN_DETECT_LIMIT, STREAMING_ENABLED, TEMPERATURE, TOP_P
            MAX_TOOL_CALLS = settings["max_tool_calls"]
            MAX_FILES_PER_SESSION = settings["max_files_per_session"]
            MAX_HISTORY_TOKENS = settings["max_history_tokens"]
            MAX_CONTEXT_TOKENS = settings["max_context_tokens"]
            KEEP_MESSAGES_ON_SUMMARY = settings["keep_messages_on_summary"]
            MAX_SESSION_HISTORY = settings["max_session_history"]
            PATTERN_DETECT_LIMIT = settings["pattern_detect_limit"]
            STREAMING_ENABLED = settings["streaming"]
            TEMPERATURE = settings["temperature"]
            TOP_P = settings["top_p"]
            
            # Azuriraj instancu
            self._max_tool_calls = MAX_TOOL_CALLS
            self._max_files_per_session = MAX_FILES_PER_SESSION
            
            self.status_label.setText(f"✅ Podešavanja sačuvana (max alata: {MAX_TOOL_CALLS}, fajlova: {MAX_FILES_PER_SESSION})")
            dlg.accept()
        
        save_btn.clicked.connect(_save_settings)
        dlg.exec_()

    def _show_models_dialog(self):
        """Dijalog za dodavanje/uklanjanje modela."""
        models = load_models_config()
        
        dlg = QDialog(self)
        dlg.setWindowTitle("🧠 DeepSeek modeli")
        dlg.setWindowIcon(get_deepseek_icon())
        dlg.setFixedSize(450, 350)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        label = QLabel("<b>Trenutni modeli:</b> Dodaj nove modele (V5, V6...) ovde:<br>"
                      "<span style='color:#888; font-size:10px;'>Model ID = ono što API očekuje (npr. deepseek-v5)</span>")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Lista modela
        self.models_list_widget = QTextEdit()
        self.models_list_widget.setPlainText(
            "\n".join(f"{m['id']} | {m['name']}" for m in models)
        )
        self.models_list_widget.setStyleSheet("background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 4px; padding: 8px; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.models_list_widget)
        
        # Info
        info = QLabel(
            '<span style="color: #888; font-size: 10px;">'
            'Format: <b>model_id | Naziv</b><br>'
            'Npr: <b>deepseek-v5-flash | DeepSeek V5 Flash</b><br>'
            'Prvi model u listi je podrazumevani (default).</span>')
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Dugmad
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Dodaj red")
        add_btn.clicked.connect(lambda: self.models_list_widget.append("novi-model-id | Novi Model"))
        btn_layout.addWidget(add_btn)

        # 🔃 Refresh iz API-ja
        refresh_btn = QPushButton("🔃 Refresh iz API-ja")
        refresh_btn.setToolTip("Dohvati sve dostupne modele direktno sa DeepSeek API-ja")
        refresh_btn.clicked.connect(lambda: self._refresh_models_from_api(dlg))
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Sačuvaj")
        save_btn.setStyleSheet("QPushButton { background: #e94560; color: white; font-weight: bold; }")
        save_btn.clicked.connect(lambda: self._save_models_from_dialog(dlg))
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✕ Odustani")
        cancel_btn.clicked.connect(dlg.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        dlg.exec_()
    
    def _save_models_from_dialog(self, dlg):
        """Čuva modele iz dijaloga u JSON fajl i osvežava combo box."""
        text = self.models_list_widget.toPlainText().strip()
        models = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 2:
                model_id = parts[0].strip()
                model_name = parts[1].strip()
                if model_id:
                    models.append({"id": model_id, "name": model_name})
        
        if not models:
            QMessageBox.warning(self, "Greška", "Nema ispravnih modela!")
            return
        
        # Prvi model je default
        models[0]["default"] = True
        for m in models[1:]:
            m["default"] = False
        
        save_models_config(models)
        
        # Osveži globalne promenljive
        global DEEPSEEK_MODELS, DEFAULT_MODEL
        DEEPSEEK_MODELS = {m["id"]: m["name"] for m in models}
        DEFAULT_MODEL = models[0]["id"]
        
        # Osveži combo box
        self.current_model = DEFAULT_MODEL
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model_id, model_name in DEEPSEEK_MODELS.items():
            self.model_combo.addItem(model_name, model_id)
        self.model_combo.blockSignals(False)
        self.model_combo.setCurrentIndex(0)
        
        self.status_label.setText(f"✅ Modeli sačuvani! Default: {DEFAULT_MODEL}")
        dlg.accept()

    def _refresh_models_from_api(self, dlg):
        """Dohvata modele sa API-ja i ažurira TextEdit u models dijalogu.
        ⚠️ ASINHRONO - ne blokira UI (QEventLoop bi zamrzao aplikaciju!)."""
        if not self.api_key:
            QMessageBox.warning(dlg, "API ključ", "Prvo podesi API ključ preko 🔑 Key dugmeta!")
            return

        log("🔃 _refresh_models_from_api() - asinhroni zahtev krece")
        # Prvo dohvati modele sa API-ja
        self.status_label.setText("🔄 Dohvatam modele sa API-ja...")
        url = QUrl(DEEPSEEK_LIST_MODELS_URL)
        request = QNetworkRequest(url)
        request.setRawHeader(b"Authorization", f"Bearer {self.api_key}".encode("utf-8"))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        reply = self.api_manager.get(request)

        # ⚠️ UMESTO QEventLoop (koji BLOKIRA UI) - koristimo asinhroni callback
        def _on_done():
            try:
                if reply.error() != QNetworkReply.NoError:
                    err_msg = reply.errorString()
                    log(f"🔃 _refresh_models_from_api - GRESKA: {err_msg[:80]}")
                    QMessageBox.warning(dlg, "Greška", f"Ne mogu da dohvatim modele:\n{err_msg}\n\nKoristim lokalne modele.")
                    self._apply_models(FALLBACK_MODELS)
                    reply.deleteLater()
                    return

                data_bytes = reply.readAll().data()
                data = json.loads(data_bytes)
                models_data = data.get("data", [])

                if not models_data:
                    log("🔃 _refresh_models_from_api - API nema modela")
                    QMessageBox.information(dlg, "Info", "API nema modele. Koristim lokalne.")
                    self._apply_models(FALLBACK_MODELS)
                    reply.deleteLater()
                    return

                # Filtriraj samo deepseek modele
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
                    if not model_id or not model_id.startswith("deepseek"):
                        continue
                    name = known_names.get(model_id, model_id.replace("-", " ").title())
                    new_models.append({"id": model_id, "name": name})

                if not new_models:
                    log("🔃 _refresh_models_from_api - nema DeepSeek modela")
                    QMessageBox.information(dlg, "Info", "API nema DeepSeek modela. Koristim lokalne.")
                    self._apply_models(FALLBACK_MODELS)
                    reply.deleteLater()
                    return

                # Ažuriraj TextEdit u dijalogu
                text_lines = "\n".join(f"{m['id']} | {m['name']}" for m in new_models)
                if hasattr(self, 'models_list_widget'):
                    self.models_list_widget.setPlainText(text_lines)

                # Sačuvaj i osveži combo box
                self._apply_models(new_models)

                log(f"🔃 _refresh_models_from_api - OK, {len(new_models)} modela")
                self.status_label.setText(f"✅ Učitano {len(new_models)} modela sa API-ja")

            except Exception as e:
                log(f"🔃 _refresh_models_from_api - GRESKA: {e}")
                QMessageBox.warning(dlg, "Greška", f"Greška pri parsiranju modela:\n{str(e)}\n\nKoristim lokalne.")
                self._apply_models(FALLBACK_MODELS)
            finally:
                try:
                    reply.deleteLater()
                except:
                    pass

        reply.finished.connect(_on_done)
