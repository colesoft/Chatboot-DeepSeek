# -*- coding: utf-8 -*-
"""history.py - HistoryMixin (cuvanje/ucitavanje sesija razgovora)."""
import os
import json
from collections import OrderedDict
from datetime import datetime
from PyQt5.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from .config import HISTORY_FILE, MAX_SESSION_HISTORY
from .i18n import SYSTEM_PROMPT
from .utils import get_deepseek_icon
from .logger import log, log_time


class HistoryMixin:
    """Cuvanje/ucitavanje sesija razgovora."""

    def _load_session_by_index(self, index, sessions):
        """Ucitava sesiju iz history-ja po indeksu i prikazuje je u chatu."""
        try:
            if index < 0 or index >= len(sessions):
                return
            session = sessions[index]
            msgs = session.get("messages", [])
            if not msgs:
                return
            self._current_session_id = session.get("session_id")  # 📜 Nastavi ISTU sesiju
            
            # Očisti trenutni chat i poruke
            self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            self.chat_display.clear()
            self._show_welcome()
            
            # Dodaj poruke iz sesije
            for msg in msgs:
                if msg["role"] == "user":
                    self._append_message("user", self._escape_html(msg["content"]))
                    self.messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    self._append_message("assistant", self._escape_html(msg["content"]))
                    self.messages.append({"role": "assistant", "content": msg["content"]})
            
            preview = session.get("preview", "?")
            timestamp = session.get("timestamp", "?")
            self.status_label.setText(f"📂 Učitana sesija od {timestamp}: {preview}")
            self._append_system_message(f"📂 <b>Učitana sesija</b> od {timestamp}")
            
        except Exception as e:
            print(f"Error loading session: {e}")
            self.status_label.setText("❌ Greška pri učitavanju sesije")

    def _get_history_path(self):
        """History fajl je u PROJECT folderu (svaki projekat ima svoj).
        ✅ Namerno - da se istorija 2-3 projekta ne meša u jednom fajlu!"""
        return os.path.join(self.project_path, HISTORY_FILE)

    def _save_history(self):
        """Čuva trenutnu sesiju u history fajl (u project folderu)."""
        log("💾 _save_history() - pocetak")
        try:
            history_path = self._get_history_path()
            file_size_mb = os.path.getsize(history_path) / 1024 / 1024 if os.path.exists(history_path) else 0
            log(f"💾 _save_history() - fajl {file_size_mb:.1f} MB")
            
            # Učitaj postojeću istoriju
            sessions = []
            if os.path.exists(history_path):
                try:
                    with open(history_path, "r", encoding="utf-8") as f:
                        sessions = json.load(f)
                except:
                    sessions = []
            
            # Ako nema poruka (samo system prompt), ne čuvaj
            user_msgs = [m for m in self.messages if m.get("role") == "user"]
            if not user_msgs:
                return False
            
            now = datetime.now()
            
            # 🔍 Ako već imamo ID trenutne sesije, pronađi je i AŽURIRAJ
            # (umesto da praviš novu sesiju svaki put - to je stvaralo duplikate!)
            updated = False
            for s in sessions:
                if s.get("session_id") == self._current_session_id:
                    s["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")
                    s["date"] = now.strftime("%Y-%m-%d")
                    s["time"] = now.strftime("%H:%M")
                    s["preview"] = user_msgs[0].get("content", "")[:80] + ("..." if len(user_msgs[0].get("content", "")) > 80 else "")
                    s["messages"] = []
                    for msg in self.messages:
                        if msg.get("role") in ("user", "assistant"):
                            s["messages"].append({
                                "role": msg["role"],
                                "content": msg.get("content", "")
                            })
                    updated = True
                    break
            
            if not updated:
                # Nova sesija - kreiraj je i zapamti ID
                session_id = now.strftime("%Y%m%d%H%M%S%f")
                self._current_session_id = session_id
                session = {
                    "session_id": session_id,
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M"),
                    "preview": user_msgs[0].get("content", "")[:80] + ("..." if len(user_msgs[0].get("content", "")) > 80 else ""),
                    "messages": []
                }
                for msg in self.messages:
                    if msg.get("role") in ("user", "assistant"):
                        session["messages"].append({
                            "role": msg["role"],
                            "content": msg.get("content", "")
                        })
                # Dodaj novu sesiju na početak
                sessions.insert(0, session)
            
            # Ograniči na MAX_SESSION_HISTORY sesija
            if len(sessions) > MAX_SESSION_HISTORY:
                sessions = sessions[:MAX_SESSION_HISTORY]
            
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            log("💾 _save_history() - KRAJ (uspeh)")
            return True
        except Exception as e:
            print("Error saving history:", e)
            log(f"💾 _save_history() - GRESKA: {e}")
            return False

    def _load_history(self):
        """Učitava poslednju sesiju iz history fajla. Ako je stari format, briše ga.
        Dodaje poruke i u self.messages da ne bi nestale pri promeni jezika."""
        log("📂 _load_history() - pocetak")
        try:
            history_path = self._get_history_path()
            if os.path.exists(history_path):
                file_size_mb = os.path.getsize(history_path) / 1024 / 1024
                log(f"📂 _load_history() - fajl {file_size_mb:.1f} MB")
                with open(history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Proveri da li je novi format (sesije sa "preview" poljem)
                if data and len(data) > 0 and isinstance(data[0], dict) and "preview" in data[0]:
                    # Novi format - učitaj prvu sesiju
                    self._current_session_id = data[0].get("session_id")  # 📜 Zapamti ID da nastavak ažurira ISTU sesiju
                    msgs = data[0].get("messages", [])
                    for msg in msgs:
                        if msg["role"] == "user":
                            self._append_message("user", self._escape_html(msg["content"]))
                            self.messages.append({"role": "user", "content": msg["content"]})
                        elif msg["role"] == "assistant":
                            self._append_message("assistant", self._escape_html(msg["content"]))
                            self.messages.append({"role": "assistant", "content": msg["content"]})
                    return msgs
                else:
                    # Stari format - obriši ga
                    os.remove(history_path)
                    print("Stari history format obrisan. Novi će se kreirati.")
        except Exception as e:
            print("Error loading history:", e)
            log(f"📂 _load_history() - GRESKA: {e}")
        return []

    def _show_history_dialog(self):
        """Prikazuje dijalog sa klikabilnom listom sesija."""
        history_path = self._get_history_path()
        if not os.path.exists(history_path):
            QMessageBox.information(self, "History", "Nema sačuvanih razgovora.")
            return

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                sessions = json.load(f)
        except:
            QMessageBox.warning(self, "Greška", "Ne mogu da čitam history fajl.")
            return

        if not sessions:
            QMessageBox.information(self, "History", "History je prazan.")
            return

        dlg = QDialog()
        dlg.setWindowTitle("📜 History razgovora")
        dlg.setWindowIcon(get_deepseek_icon())
        dlg.resize(650, 550)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Naslov
        title = QLabel(f"<b>📜 History razgovora</b> ({len(sessions)} sesija)")
        title.setStyleSheet("color: #e94560; font-size: 14px;")
        layout.addWidget(title)

        # Lista sesija
        list_widget = QListWidget()
        list_widget.setStyleSheet("""
            QListWidget { background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 6px; font-size: 11px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #1a1a3e; }
            QListWidget::item:selected { background: #0f3460; color: #e94560; }
            QListWidget::item:hover { background: #1a1a3e; }
        """)

        # Popuni listu
        session_items = []
        from collections import OrderedDict
        groups = OrderedDict()
        for s in sessions:
            date = s.get("date", "")
            if date not in groups:
                groups[date] = []
            groups[date].append(s)

        all_session_list = []
        for date, sess_list in groups.items():
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                day_name = ["Pon", "Uto", "Sre", "Čet", "Pet", "Sub", "Ned"][dt.weekday()]
                header = f"📅 {dt.day}.{dt.month}.{dt.year}. ({day_name})"
            except:
                header = f"📅 {date}"
            
            h_item = QListWidgetItem(header)
            h_item.setForeground(QColor("#e94560"))
            h_item.setFlags(h_item.flags() & ~Qt.ItemIsSelectable)
            f = h_item.font()
            f.setBold(True)
            h_item.setFont(f)
            list_widget.addItem(h_item)
            
            for sess in sess_list:
                time = sess.get("time", "")
                msgs = sess.get("messages", [])
                user_txt = ""
                for m in msgs:
                    if m["role"] == "user":
                        user_txt = m.get("content", "")[:100]
                        break
                disp = f"🕐 {time}  👤 {user_txt}" if user_txt else f"🕐 {time}"
                
                s_item = QListWidgetItem(disp)
                s_item.setForeground(QColor("#d4d4d4"))
                s_item.setData(Qt.UserRole, sess)
                list_widget.addItem(s_item)
                all_session_list.append(sess)

        layout.addWidget(list_widget)

        # Info i dugmad
        info = QLabel('<span style="color: #888; font-size: 10px;">Klikni na sesiju pa na "Učitaj" ili dvoklikni.</span>')
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        load_btn = QPushButton("📂 Učitaj sesiju")
        load_btn.setStyleSheet("QPushButton { background: #e94560; color: white; font-weight: bold; border-radius: 6px; padding: 8px 20px; }")

        def _load_sel():
            item = list_widget.currentItem()
            if not item or not item.data(Qt.UserRole):
                QMessageBox.information(dlg, "Info", "Izaberi sesiju iz liste.")
                return
            sess = item.data(Qt.UserRole)
            self._load_session_data(sess)
            dlg.accept()

        load_btn.clicked.connect(_load_sel)
        btn_layout.addWidget(load_btn)

        def _double_click(index):
            # ⚠️ PyQt5 doubleClicked šalje QModelIndex, ne int!
            item = list_widget.item(index.row())
            if item and item.data(Qt.UserRole):
                self._load_session_data(item.data(Qt.UserRole))
                dlg.accept()

        list_widget.doubleClicked.connect(_double_click)

        cancel_btn = QPushButton("✕ Zatvori")
        cancel_btn.clicked.connect(dlg.accept)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dlg.exec_()

    def _load_session_data(self, session):
        """Ucitava sesiju u chat."""
        try:
            msgs = session.get("messages", [])
            if not msgs:
                return
            self._current_session_id = session.get("session_id")  # 📜 Nastavi ISTU sesiju
            self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            self.chat_display.clear()
            self._show_welcome()
            for msg in msgs:
                role, content = msg.get("role", ""), msg.get("content", "")
                if role == "user":
                    self._append_message("user", self._escape_html(content))
                    self.messages.append({"role": "user", "content": content})
                elif role == "assistant":
                    self._append_message("assistant", self._escape_html(content))
                    self.messages.append({"role": "assistant", "content": content})
            ts = session.get("timestamp", "?")
            pv = session.get("preview", "?")
            self.status_label.setText(f"📂 Učitana sesija od {ts}: {pv}")
            self._append_system_message(f"📂 <b>Učitana sesija</b> od {ts}")
        except Exception as e:
            print("Error loading session:", e)
            self.status_label.setText("❌ Greška pri učitavanju")

    # -------------------------------------------------------------------------
