# DeepSeek Code Assistant - Kao QodeAssist, ali tvoj sopstveni
# -----------------------------------------------------------
# PyQt5 aplikacija koja koristi DeepSeek API function calling
# za citanje, editovanje i pretragu fajlova u Qt Creator projektu.
#
# Pokretanje (instaliraj PyQt5 prvi put):
#   python -m pip install PyQt5
#   python deepseek_chatbot.py
#
# Sta moze:
#   📂 list_files     - Lista sve fajlove u projektu
#   📖 read_file      - Cita fajl sa brojevima linija
#   ✏️ edit_file      - Menja deo fajla (uz diff potvrdu!)
#   📄 create_file    - Kreira novi fajl (uz potvrdu)
#   🔍 search_text    - Pretrazuje tekst u fajlovima
#   📋 read_log       - Cita build logove
#   ⚡ run_command    - Pokrece build, git, itd.
#   🐛 get_issues     - Cita build greške
#
# Bezbednost:
#   - Sve izmene zahtevaju korisnicku potvrdu
#   - Prikazuje diff pre editovanja
#   - Pravljenje backup fajlova (.bak)
#   - Radi SAMO unutar projektnog direktorijuma

TEMPLATE = app
CONFIG += console c++17
CONFIG -= app_bundle
CONFIG -= qt

