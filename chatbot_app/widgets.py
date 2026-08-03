# -*- coding: utf-8 -*-
"""
widgets.py - Dijalozi i widgeti
================================
- DiffDialog: prikaz starog/novog teksta pre potvrde izmene
- (u budućnosti: SplashScreen, EmojiPicker, HistoryDialog)
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSplitter, QWidget, QPlainTextEdit,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt


class DiffDialog(QDialog):
    """Dijalog koji prikazuje diff pre nego što se primeni izmena."""

    def __init__(self, title, filepath, old_text, new_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Info
        info = QLabel(f"<b>File:</b> {filepath}")
        layout.addWidget(info)

        # Splitter: stari vs novi
        splitter = QSplitter(Qt.Horizontal)

        # Stari tekst
        old_widget = QWidget()
        old_layout = QVBoxLayout(old_widget)
        old_layout.setContentsMargins(0, 0, 0, 0)
        old_layout.addWidget(QLabel("⬅️ Stari tekst (biće zamenjen):"))
        old_edit = QPlainTextEdit(old_text)
        old_edit.setReadOnly(True)
        old_edit.setStyleSheet("background-color: #fff0f0; color: #800; font-family: monospace;")
        old_layout.addWidget(old_edit)
        splitter.addWidget(old_widget)

        # Novi tekst
        new_widget = QWidget()
        new_layout = QVBoxLayout(new_widget)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.addWidget(QLabel("➡️ Novi tekst:"))
        new_edit = QPlainTextEdit(new_text)
        new_edit.setReadOnly(True)
        new_edit.setStyleSheet("background-color: #f0fff0; color: #080; font-family: monospace;")
        new_layout.addWidget(new_edit)
        splitter.addWidget(new_widget)

        layout.addWidget(splitter)

        # Dugmad
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("✅ Primeni")
        buttons.button(QDialogButtonBox.Cancel).setText("❌ Odustani")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setModal(True)
