# -*- coding: utf-8 -*-
"""
DeepSeek Code Assistant - chatbot_app paket
Podeljen na manje module radi lakseg odrzavanja:

- config.py    : OS detekcija, putanje, settings, modeli, API konstante
- i18n.py      : Prevodi (sr/rs/en/zh), ABOUT, SYSTEM_PROMPT
- utils.py     : Ikona, API kljuc, putanje projekta, helper funkcije
- tools.py     : ToolExecutor + tool definicije za DeepSeek API
- widgets.py   : DiffDialog (i drugi dijaloci u buducnosti)
- api_client.py: (Faza 2) DeepSeek API klijent
- history.py   : (Faza 2) Cuvanje/ucitavanje istorije
- ui/          : (Faza 3) ChatWindow, dijalozi, tema
"""

__version__ = "1.0.0"
APP_NAME = "DeepSeek assistant by Cole_soft Krusevac"
