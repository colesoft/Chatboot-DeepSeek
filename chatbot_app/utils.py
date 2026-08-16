# -*- coding: utf-8 -*-
"""
utils.py - Pomocne funkcije
============================
- get_deepseek_icon: DeepSeek ikonica (kreira ako ne postoji)
- load_api_key / save_api_key
- load_project_path / save_project_path
- is_within_project: bezbednosna provera putanje
- escape_html: HTML escape za chat poruke
"""

import os

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QIcon, QPixmap

from .config import IS_WINDOWS, IS_LINUX, ICON_EXT, get_data_file

# =============================================================================
DEEPSEEK_ICON = None  # biće kreiran posle QApplication


def get_deepseek_icon():
    """Vraća DeepSeek ikonicu (kreira je ako treba).
    - Windows: .ico format
    - Linux: .png format
    """
    global DEEPSEEK_ICON
    if DEEPSEEK_ICON is None:
        img_dir = os.path.dirname(os.path.abspath(__file__))

        # Pokušaj sa odgovarajućom ekstenzijom za OS
        icon_file = os.path.join(img_dir, f"deepseek{ICON_EXT}")
        if os.path.exists(icon_file):
            DEEPSEEK_ICON = QIcon(icon_file)
            return DEEPSEEK_ICON

        # Probaj i drugu ekstenziju
        alt_ext = ".png" if ICON_EXT == ".ico" else ".ico"
        icon_file = os.path.join(img_dir, f"deepseek{alt_ext}")
        if os.path.exists(icon_file):
            DEEPSEEK_ICON = QIcon(icon_file)
            return DEEPSEEK_ICON

        # Inače kreiraj programski
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#0f3460"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        icon_font_name = "Ubuntu" if IS_LINUX else "Segoe UI"
        font = QFont(icon_font_name, 32, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#0f3460"))
        painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "D")
        painter.end()

        # Sačuvaj za sledeći put
        try:
            save_path = os.path.join(img_dir, f"deepseek{ICON_EXT}")
            if IS_WINDOWS:
                pixmap.save(save_path, "ICO")
            else:
                pixmap.save(save_path, "PNG")
        except:
            pass

        DEEPSEEK_ICON = QIcon(pixmap)
    return DEEPSEEK_ICON


def load_api_key():
    """Ucitava API kljuc iz env varijable ili fajla."""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    config_path = get_data_file("api_key.txt")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            key = f.read().strip()
            if key:
                return key
    return ""


def load_project_path():
    """Ucitava putanju projekta iz config fajla."""
    config_path = get_data_file("project_path.txt")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            path = f.read().strip()
            if path and os.path.isdir(path):
                return path
    return os.path.dirname(os.path.abspath(__file__))


def save_project_path(path):
    """Cuvamo putanju projekta u config fajl."""
    with open(get_data_file("project_path.txt"), "w") as f:
        f.write(path)


def is_within_project(filepath, project_path):
    """Proverava da li je fajl unutar projektnog direktorijuma."""
    abs_file = os.path.abspath(filepath)
    abs_project = os.path.abspath(project_path)
    return abs_file.startswith(abs_project)


def escape_html(text):
    """Escape HTML specijalne karaktere (za siguran prikaz korisničkog unosa)."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            )


def estimate_tokens(text):
    """Gruba procena broja tokena (4 karaktera ≈ 1 token)."""
    return len(text) // 4


def count_context_tokens(messages):
    """Vraća procenjen broj tokena svih poruka u listi.

    Uključuje i tool_calls (zauzimaju prostor u kontekstu).
    """
    import json as _json

    total = 0
    for msg in messages:
        content = msg.get("content", "") or ""
        if isinstance(content, list):
            # 🖼️ OpenAI-style content list (text + image_url delovi)
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        total += estimate_tokens(part.get("text", "") or "")
                    elif part.get("type") == "image_url":
                        # Slike se broje kao fiksan broj tokena (base64 se ne šalje u procenu)
                        total += 1000
                elif isinstance(part, str):
                    total += estimate_tokens(part)
        else:
            total += estimate_tokens(content)
        # Tool callovi i rezultati takođe zauzimaju prostor
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                total += estimate_tokens(_json.dumps(tc))
    return total


def short_path(path, max_len=40):
    """Skraćuje putanju za prikaz (sa ... na početku)."""
    if len(path) <= max_len:
        return path
    return "..." + path[-(max_len - 3):]
