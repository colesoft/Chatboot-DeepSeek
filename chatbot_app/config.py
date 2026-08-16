# -*- coding: utf-8 -*-
"""
config.py - Konfiguracija aplikacije
=====================================
- OS detekcija (Windows / Linux / Mac)
- Folderi za podatke (AppData / .config)
- Settings management (JSON)
- Modeli (cache iz models.json + fallback)
- DeepSeek API endpointi
"""

import os
import json
import sys

# =============================================================================
# OS DETEKCIJA (Windows / Linux / Mac)
# =============================================================================
IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform.startswith("darwin")

if IS_LINUX:
    import platform
    # Na Linux-u proveravamo da li je X11 ili Wayland
    IS_X11 = os.environ.get("XDG_SESSION_TYPE", "").lower() == "x11"
    # Fontovi na Linux-u
    DEFAULT_FONT = "Ubuntu, Noto Sans, DejaVu Sans, sans-serif"
    FONT_NAME = "Ubuntu"
    ICON_EXT = ".png"
else:
    IS_X11 = True
    DEFAULT_FONT = "Segoe UI, Roboto, sans-serif"
    FONT_NAME = "Segoe UI"
    ICON_EXT = ".ico"

APP_NAME = "DeepSeek assistant by Cole_soft Krusevac"


# =============================================================================
# POMOCNE FUNKCIJE ZA PUTANJE
# =============================================================================

def get_data_dir():
    """Vraća folder za čuvanje podataka (history, modeli, itd.).
    - Windows: %APPDATA%/ColeSoft/DeepSeekAssistant
    - Linux: ~/.config/ColeSoft/DeepSeekAssistant
    - Mac: ~/Library/ColeSoft/DeepSeekAssistant
    """
    if IS_WINDOWS:
        base = os.environ.get('APPDATA', '')
        if not base:
            base = os.path.expanduser('~')
    elif IS_MAC:
        base = os.path.expanduser('~/Library')
    else:  # Linux
        base = os.environ.get('XDG_CONFIG_HOME', '')
        if not base:
            base = os.path.expanduser('~/.config')
    data_dir = os.path.join(base, 'ColeSoft', 'DeepSeekAssistant')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_data_file(filename):
    """Vraća punu putanju do fajla u data folderu."""
    return os.path.join(get_data_dir(), filename)


def get_app_dir():
    """Vraća folder gde je APLIKACIJA (main.py / deepseek_chatbot.py).

    ⚠️ VAŽNO: Ne koristiti project_path! History i context se čuvaju
    u folderu aplikacije, NE u folderu projekta na kome se radi.
    """
    here = os.path.dirname(os.path.abspath(__file__))  # .../chatbot_app/
    parent = os.path.dirname(here)
    # Proveri da li je parent zaista app folder (ima main.py ili deepseek_chatbot.py)
    for f in ("main.py", "deepseek_chatbot.py"):
        if os.path.exists(os.path.join(parent, f)):
            return parent
    return parent


# =============================================================================
# DEEPSEEK API ENDPOINT-I (iz https://api-docs.deepseek.com/)
# =============================================================================
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_BETA_API_URL = "https://api.deepseek.com/beta/chat/completions"
DEEPSEEK_COMPLETIONS_URL = "https://api.deepseek.com/completions"
DEEPSEEK_BETA_COMPLETIONS_URL = "https://api.deepseek.com/beta/completions"
DEEPSEEK_LIST_MODELS_URL = "https://api.deepseek.com/models"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"
DEEPSEEK_MODEL = "deepseek-v4-flash"

# Podržani modeli (iz API docs)
DEEPSEEK_SUPPORTED_MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]


# =============================================================================
# SETTINGS MANAGEMENT (podesavanja koja korisnik menja kroz UI)
# =============================================================================
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "max_tool_calls": 50,          # Max alata po poruci pre forced stop
    "max_files_per_session": 10,   # Max fajlova pre nego sto auto-apply iskljuci
    "max_history_tokens": 8000,    # Tokeni pre sazimanja (po user/assistant porukama)
    "max_context_tokens": 800000,  # Apsolutni limit contexta za API
    "max_session_history": 50,     # Max sesija u history fajlu
    "keep_messages_on_summary": 10, # Koliko poruka sacuvati posle sazimanja
    "pattern_detect_limit": 50,    # Pattern detekcija: min 20, max 10000 (0 = iskljuceno)
    "streaming": True,             # Streaming odgovora (reč po reč)
    "temperature": 0.3,            # Kreativnost modela (0.0 - 2.0)
    "top_p": 0.9,                  # Top P sampling (0.0 - 1.0)
    "show_thinking": True,          # Prikaži "DeepSeek razmišlja..." pre odgovora
    # 📬 Gmail – provera nepročitanih email-ova pre slanja
    "gmail_enabled": False,        # Da li se proverava Gmail pre svake poruke
    "gmail_user": "",              # Gmail adresa (npr. tvoj.mail@gmail.com)
    "gmail_app_password": "",      # Google App Password (16 znakova) - NIJE obična lozinka!
    "gmail_search_query": "",      # Opcioni Gmail search upit (from:, subject:, is:unread...)
}


def load_settings():
    """Ucitava settings iz JSON fajla. Ako ne postoji, kreira default."""
    path = get_data_file(SETTINGS_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Proveri da li svi kljucevi postoje
            if isinstance(data, dict):
                for k in DEFAULT_SETTINGS:
                    if k not in data:
                        data[k] = DEFAULT_SETTINGS[k]
                return data
        except:
            pass
    # Default
    save_settings(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    """Cuvamo settings u JSON fajl."""
    with open(get_data_file(SETTINGS_FILE), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# Ucitaj settings odmah
_settings = load_settings()
MAX_TOOL_CALLS = _settings["max_tool_calls"]
MAX_FILES_PER_SESSION = _settings["max_files_per_session"]
MAX_HISTORY_TOKENS = _settings["max_history_tokens"]
MAX_CONTEXT_TOKENS = _settings["max_context_tokens"]
MAX_SESSION_HISTORY = _settings["max_session_history"]
KEEP_MESSAGES_ON_SUMMARY = _settings["keep_messages_on_summary"]
PATTERN_DETECT_LIMIT = _settings["pattern_detect_limit"]
STREAMING_ENABLED = _settings.get("streaming", True)
TEMPERATURE = _settings.get("temperature", 0.3)
TOP_P = _settings.get("top_p", 0.9)

# History management
MAX_HISTORY_MESSAGES = 50
HISTORY_FILE = "deepseek_history.json"
MODELS_CONFIG_FILE = "models.json"
SESSION_FILE = "session_backup.json"  # Za save/load po imenu


def load_models_config():
    """Učitava modele iz JSON fajla.
    - Ako postoji 'models.json' u AppData, koristi ga (cache sa API-ja)
    - Ako ne postoji, vraća praznu listu - API će ih pokušati učitati,
      a ako API ne radi, koristi se fallback u _on_models_api_reply
    """
    path = get_data_file(MODELS_CONFIG_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except:
            pass
    return []


def save_models_config(models):
    with open(get_data_file(MODELS_CONFIG_FILE), "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)


# Fallback modeli ako API ne radi (DeepSeek nema /list-models endpoint)
FALLBACK_MODELS = [
    {"id": "deepseek-chat", "name": "DeepSeek V3 (preporučen)", "default": True},
    {"id": "deepseek-reasoner", "name": "DeepSeek R1", "default": False},
    {"id": "deepseek-coder", "name": "DeepSeek Coder", "default": False},
]

# Učitaj modele (iz cache-a ili prazno)
_models_list = load_models_config()
if _models_list:
    DEEPSEEK_MODELS = {m["id"]: m["name"] for m in _models_list}
    DEFAULT_MODEL = next((m["id"] for m in _models_list if m.get("default")), _models_list[0]["id"])
else:
    # Privremeno loading - biće zamenjeno sa API-ja ili fallback-om
    DEEPSEEK_MODELS = {"loading": "🔄 Učitavam modele..."}
    DEFAULT_MODEL = "loading"
