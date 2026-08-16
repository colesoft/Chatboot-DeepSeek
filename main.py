#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Ulazna tacka aplikacije
==================================
Kreira QApplication, tamnu paletu, splash screen i pokrece ChatWindow.

Pokretanje:
    python main.py
"""

import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import (
    QPalette, QColor, QPixmap, QPainter, QFont, QPen, QLinearGradient,
)

from chatbot_app.config import IS_WINDOWS, FONT_NAME
from chatbot_app.utils import get_deepseek_icon
from deepseek_chatbot import ChatWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Taskbar ikona - OBAVEZNO pre bilo kog prozora!
    app.setWindowIcon(get_deepseek_icon())

    # Moderna tamna paleta
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1a1a2e"))
    palette.setColor(QPalette.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Base, QColor("#16213e"))
    palette.setColor(QPalette.AlternateBase, QColor("#1a1a2e"))
    palette.setColor(QPalette.ToolTipBase, QColor("#16213e"))
    palette.setColor(QPalette.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.Button, QColor("#0f3460"))
    palette.setColor(QPalette.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.BrightText, QColor("#ff6b6b"))
    palette.setColor(QPalette.Highlight, QColor("#e94560"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # Globalni stil - moderan, čist, tamna tema
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1a1a2e;
        }
        QWidget {
            font-family: 'Segoe UI', 'SF Pro Display', 'Roboto', sans-serif;
        }
        QPushButton {
            background-color: #0f3460;
            color: #e0e0e0;
            border: none;
            border-radius: 6px;
            padding: 7px 16px;
            font-size: 12px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #1a4a7a;
            border: 1px solid #e94560;
        }
        QPushButton:pressed {
            background-color: #0a2647;
        }
        QPushButton:disabled {
            background-color: #2a2a3e;
            color: #666;
        }
        QLineEdit {
            background-color: #16213e;
            color: #e0e0e0;
            border: 2px solid #0f3460;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            selection-background-color: #e94560;
        }
        QLineEdit:focus {
            border-color: #e94560;
        }
        QComboBox {
            background-color: #0f3460;
            color: #e0e0e0;
            border: 1px solid #1a4a7a;
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 11px;
        }
        QComboBox:hover {
            border-color: #e94560;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background-color: #16213e;
            color: #e0e0e0;
            selection-background-color: #0f3460;
            selection-color: #e94560;
            border: 1px solid #0f3460;
        }
        QTextEdit {
            background-color: #16213e;
            color: #e0e0e0;
            border: none;
            border-radius: 0px;
            padding: 4px;
            font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
        }
        QLabel {
            color: #e0e0e0;
        }
        QScrollBar:vertical {
            background-color: #1a1a2e;
            width: 8px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background-color: #0f3460;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #e94560;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background-color: #1a1a2e;
            height: 8px;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background-color: #0f3460;
            border-radius: 4px;
            min-width: 30px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #e94560;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QDialog {
            background-color: #1a1a2e;
        }
        QMessageBox {
            background-color: #1a1a2e;
        }
        QInputDialog {
            background-color: #1a1a2e;
        }
        QFileDialog {
            background-color: #1a1a2e;
        }
        QSplitter::handle {
            background-color: #0f3460;
            width: 1px;
        }
        QFrame {
            border: none;
        }
    """)

    # =========================================================================
    # SPLASH SCREEN - pre nego što se prikaže glavni prozor
    # =========================================================================
    splash_pix = QPixmap(560, 380)
    splash_pix.fill(QColor("#0f3460"))
    
    p = QPainter(splash_pix)
    p.setRenderHint(QPainter.Antialiasing)
    
    # Gradijent pozadina
    grad = QLinearGradient(0, 0, 560, 380)
    grad.setColorAt(0.0, QColor("#0f3460"))
    grad.setColorAt(0.5, QColor("#16213e"))
    grad.setColorAt(1.0, QColor("#0a2647"))
    p.fillRect(0, 0, 560, 380, grad)
    
    # Okvir
    pen = QPen(QColor("#e94560"))
    pen.setWidth(2)
    p.setPen(pen)
    p.drawRoundedRect(5, 5, 550, 370, 12, 12)
    
    # Linija 1: DeepSeek ❤️ Cole_Soft
    font1 = QFont(FONT_NAME, 24, QFont.Bold)
    p.setFont(font1)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRect(0, 45, 560, 55), Qt.AlignCenter, "🤖 DeepSeek  ❤️  Cole_Soft")
    
    # Linija 2: Zastave - učitaj slike, inače nacrtaj programski
    flag_y = 110
    flag_h = 65
    flag_w = 85
    
    # Probaj da učitaš slike zastava
    img_dir = os.path.dirname(os.path.abspath(__file__))
    rs_img = QPixmap(os.path.join(img_dir, "rs.jpg"))
    cn_img = QPixmap(os.path.join(img_dir, "cn.jpg"))
    
    has_rs = not rs_img.isNull()
    has_cn = not cn_img.isNull()
    
    if has_rs:
        # Prikaži sliku Srbije - veća!
        scaled_rs = rs_img.scaled(flag_w, flag_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(130, flag_y, scaled_rs)
    else:
        # Nacrtaj trobojku
        flag_srb_x = 145
        stripe_w = 16
        p.fillRect(flag_srb_x, flag_y, stripe_w, flag_h, QColor("#c6363c"))
        p.fillRect(flag_srb_x+stripe_w, flag_y, stripe_w, flag_h, QColor("#003580"))
        p.fillRect(flag_srb_x+stripe_w*2, flag_y, stripe_w, flag_h, QColor("#ffffff"))
    
    # 🤝
    font_hand = QFont(FONT_NAME, 32, QFont.Bold)
    p.setFont(font_hand)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRect(215, flag_y-3, 130, flag_h+6), Qt.AlignCenter, "🤝")
    
    if has_cn:
        # Prikaži sliku Kine - veća!
        scaled_cn = cn_img.scaled(flag_w, flag_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(345, flag_y, scaled_cn)
    else:
        # Nacrtaj crvenu sa zvezdama
        flag_cn_x = 350
        flag_cn_w = flag_w
        p.fillRect(flag_cn_x, flag_y, flag_cn_w, flag_h, QColor("#de2910"))
        p.setPen(QColor("#ffde00"))
        font_big = QFont(FONT_NAME, 18, QFont.Bold)
        p.setFont(font_big)
        p.drawText(QRect(flag_cn_x+4, flag_y+2, 28, 28), Qt.AlignCenter, "★")
        font_small = QFont(FONT_NAME, 12, QFont.Bold)
        p.setFont(font_small)
        p.drawText(QRect(flag_cn_x+24, flag_y+2, 18, 18), Qt.AlignCenter, "★")
        p.drawText(QRect(flag_cn_x+36, flag_y+10, 18, 18), Qt.AlignCenter, "★")
        p.drawText(QRect(flag_cn_x+34, flag_y+26, 18, 18), Qt.AlignCenter, "★")
        p.drawText(QRect(flag_cn_x+24, flag_y+36, 18, 18), Qt.AlignCenter, "★")
    
    # SRBIJA i KINA natpisi
    font_label = QFont(FONT_NAME, 14, QFont.Bold)
    p.setFont(font_label)
    p.setPen(QColor("#e94560"))
    p.drawText(QRect(120, flag_y+flag_h+3, 110, 25), Qt.AlignCenter, "🇷🇸 SRBIJA")
    p.setPen(QColor("#ffd700"))
    p.drawText(QRect(335, flag_y+flag_h+3, 110, 25), Qt.AlignCenter, "🇨🇳 KINA")
    
    # Središnji tekst
    font3 = QFont(FONT_NAME, 18, QFont.Bold)
    p.setFont(font3)
    p.setPen(QColor("#e94560"))
    p.drawText(QRect(0, 205, 560, 40), Qt.AlignCenter, "ČELIČNO PRIJATELJSTVO")
    
    # Podnaslovi
    font4 = QFont(FONT_NAME, 12, QFont.Normal)
    p.setFont(font4)
    p.setPen(QColor("#a0a0b0"))
    p.drawText(QRect(0, 245, 560, 30), Qt.AlignCenter, "钢铁般的友谊 · Iron Friendship")
    p.drawText(QRect(0, 270, 560, 30), Qt.AlignCenter, "Srpsko-kinesko prijateljstvo traje večno!")
    
    # Powered by linija
    font5 = QFont(FONT_NAME, 9, QFont.Normal)
    p.setFont(font5)
    p.setPen(QColor("#888"))
    p.drawText(QRect(0, 310, 560, 20), Qt.AlignCenter, "🧠 Powered by DeepSeek API · Cole_Soft © 2026")
    p.drawText(QRect(0, 333, 560, 20), Qt.AlignCenter, "深圳 · 中国 · 世界 · Kruševac · Srbija")
    
    # Loading indikator
    p.setPen(QColor("#6a9955"))
    p.drawText(QRect(0, 357, 560, 20), Qt.AlignCenter, "⏳ Učitavam...")
    p.drawText(QRect(0, 333, 560, 20), Qt.AlignCenter, "深圳 · 中国 · 世界 · Kruševac · Srbija")
    
    # Loading indikator
    p.setPen(QColor("#6a9955"))
    p.drawText(QRect(0, 357, 560, 20), Qt.AlignCenter, "⏳ Učitavam...")
    
    p.end()
    
    splash = QSplashScreen(splash_pix)
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
    splash.setWindowIcon(get_deepseek_icon())
    splash.show()
    app.processEvents()
    
    print("[DEBUG] Before ChatWindow()")
    try:
        window = ChatWindow()
        print("[DEBUG] After ChatWindow() - OK")
    except Exception as e:
        print(f"[DEBUG] ChatWindow() ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Taskbar ikona - samo na Windows-u (mora POSLE show())
    if IS_WINDOWS:
        try:
            import ctypes
            myappid = u'colesoft.deepseek.assistant.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    app.setWindowIcon(get_deepseek_icon())
    
    # Glavni prozor se prikazuje TEK kada se splash zatvori
    # (klikom na splash ILI automatski posle zadate pauze)
    def show_main_window():
        splash.close()              # zatvori splash ako još nije
        window.show()               # tek sada prikaži glavni prozor
        print("[DEBUG] Main window shown after splash closed")

    # Klik na splash = odmah zatvori splash i prikaži glavni prozor
    splash.mousePressEvent = lambda event: show_main_window()

    # Automatski zatvori splash posle 10 sekundi i prikaži glavni prozor
    QTimer.singleShot(4000, show_main_window)

    print("[DEBUG] Splash visible, waiting to close...")
    app.setWindowIcon(get_deepseek_icon())
    print("[DEBUG] Before exec_()")
    sys.exit(app.exec_())
    print("[DEBUG] After exec_() - should never print")

if __name__ == "__main__":
    main()
