# -*- coding: utf-8 -*-
"""
theme.py - QSS stilovi (CSS za Qt widgete)
============================================
Svi stilovi na jednom mestu - lako menjanje boja/tema.
"""

# Glavne boje aplikacije
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_input": "#16213e",
    "bg_hover": "#1a2a4e",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "border": "#0f3460",
    "border_hover": "#2a2a5e",
    "text": "#e0e0e0",
    "text_dim": "#888",
    "success": "#6a9955",
    "warning": "#dcdcaa",
}

# Dugme "Pošalji" (normalno stanje)
SEND_BTN_ACTIVE = """
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
"""

# Dugme "STOP" (dok AI radi)
SEND_BTN_STOP = """
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
"""

# Polje za unos poruke
INPUT_FIELD = """
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
"""

# Chat display (istorija poruka)
CHAT_DISPLAY = """
    QTextEdit {
        background-color: #16213e;
        color: #e0e0e0;
        border: none;
        padding: 12px;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 13px;
        line-height: 1.5;
    }
"""

# Model combo (padajuća lista)
MODEL_COMBO = """
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
"""
