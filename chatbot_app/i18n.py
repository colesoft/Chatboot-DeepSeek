# -*- coding: utf-8 -*-
"""
i18n.py - Internacionalizacija (prevodi) + SYSTEM_PROMPT
=========================================================
- ABOUT_TEXT (3 jezika)
- LANGUAGES (srpski / english / 中文)
- save_language / load_language
- SYSTEM_PROMPT za DeepSeek model
"""

import os

from .config import get_data_file

LANG_FILE = "language.txt"

# About informacije
ABOUT_TEXT = {
    "srpski": """<h2>🤖 DeepSeek Code Assistant</h2>
<p><b>Verzija:</b> 1.0.0</p>
<p><b>Autor:</b> Cole_Soft © 2026</p>
<p><b>Web:</b> <a href='https://www.colesoft.net' style='color: #e94560;'>www.colesoft.net</a></p>
<p>🧠 Pokreće ga <b>DeepSeek</b> – najbolji AI model,
kreiran od strane <b>DeepSeek Company</b> (深度求索), Kina.</p>
<p>❤️ Napravljeno s ljubavlju prema Kini,
srpskom narodu i celom svetu!</p>
<hr style='border-color: #e94560;'>
<p style='font-size: 11px; color: #888;'>
深圳 · 中国 · 世界<br>
Od Cole_Soft-a, za sve koji vole kvalitetan kod.</p>""",

    "english": """<h2>🤖 DeepSeek Code Assistant</h2>
<p><b>Version:</b> 1.0.0</p>
<p><b>Author:</b> Cole_Soft © 2026</p>
<p><b>Web:</b> <a href='https://www.colesoft.net' style='color: #e94560;'>www.colesoft.net</a></p>
<p>🧠 Powered by <b>DeepSeek</b> – the best AI model,
created by <b>DeepSeek Company</b> (深度求索), China.</p>
<p>❤️ Made with love for China,
the Serbian people, and the whole world!</p>
<hr style='border-color: #e94560;'>
<p style='font-size: 11px; color: #888;'>
Shenzhen · China · World<br>
From Cole_Soft, for everyone who loves quality code.</p>""",

    "中文": """<h2>🤖 DeepSeek 代码助手</h2>
<p><b>版本：</b> 1.0.0</p>
<p><b>作者：</b> Cole_Soft © 2026</p>
<p><b>网站：</b> <a href='https://www.colesoft.net' style='color: #e94560;'>www.colesoft.net</a></p>
<p>🧠 由 <b>DeepSeek 公司</b>（深度求索）创建的最强AI模型驱动</p>
<p>❤️ 满怀对中国的热爱、对塞尔维亚人民的热爱、
对全世界的热爱而制作！</p>
<hr style='border-color: #e94560;'>
<p style='font-size: 11px; color: #888;'>
深圳 · 中国 · 世界<br>
来自 Cole_Soft，献给所有热爱优质代码的人。</p>"""
}


# =============================================================================
# JEZICI - PREVODI
# =============================================================================
LANGUAGES = {
    "srpski": {
        "flag": "🇷🇸", "open": "📂 Otvori", "key": "🔑 Ključ", "models": "🧠 Modeli",
        "history": "📜 Istorija", "new": "🗑️ Novi",
        "send": "▶ Pošalji", "thinking": "DeepSeek razmišlja...",
        "placeholder": "Napiši šta treba uraditi... (Enter = pošalji)",
        "hint": "💡 Npr: 'pokaži main.cpp', 'popravi grešku', 'nađi QString'",
        "project": "📁 ", "status_ready": "✅ Spremno", "status_ok": "✅ Odgovor primljen",
        "status_error": "❌ Greška", "status_cleared": "🗑️ Razgovor obrisan",
        "status_saved": "✅ API ključ sačuvan",
        "welcome_title": "🤖 DeepSeek Code Assistant",
        "welcome_sub": "🤖 DeepSeek V4 Flash",
        "welcome_hint": "Napiši šta treba uraditi",
        "diff_title": "✏️ Potvrda izmene", "diff_old": "⬅️ Stari tekst:", "diff_new": "➡️ Novi tekst:",
        "diff_apply": "✅ Primeni", "diff_cancel": "❌ Odustani",
        "history_title": "📜 Istorija razgovora", "history_empty": "Nema sačuvanih razgovora.",
        "history_error": "Ne mogu da čitam istoriju.", "history_prazan": "Istorija je prazna.",
        "about_title": "💖 O programu / About / 关于",
        "about_close": "✕ Zatvori",
        "model_title": "🧠 DeepSeek modeli", "model_label": "<b>Trenutni modeli:</b> Dodaj nove (V5, V6...) ovde:",
        "model_info": "Format: <b>model_id | Naziv</b><br>Npr: <b>deepseek-v5 | DeepSeek V5</b><br>Prvi model je podrazumevani.",
        "model_add": "➕ Dodaj red", "model_save": "💾 Sačuvaj", "model_cancel": "✕ Odustani",
        "model_empty": "Nema ispravnih modela!", "model_saved": "✅ Modeli sačuvani!",
        "key_title": "🔑 API Ključ", "key_label": "Unesi svoj DeepSeek API ključ:",
        "key_empty": "API ključ ne sme biti prazan!",
        "file_confirm": "📄 Kreiranje fajla", "file_confirm_text": "Da li želiš da kreiram novi fajl?",
        "api_missing": "API ključ nije podešen!",
        "status_model": "🧠 Model: ",
        "create_file_header": "📄 Kreiranje fajla",
    },
    "english": {
        "flag": "🇬🇧", "open": "📂 Open", "key": "🔑 Key", "models": "🧠 Models",
        "history": "📜 History", "new": "🗑️ New",
        "send": "▶ Send", "thinking": "DeepSeek thinking...",
        "placeholder": "What needs to be done? (Enter = send)",
        "hint": "💡 E.g.: 'show main.cpp', 'fix error', 'find QString'",
        "project": "📁 ", "status_ready": "✅ Ready", "status_ok": "✅ Response received",
        "status_error": "❌ Error", "status_cleared": "🗑️ Chat cleared",
        "status_saved": "✅ API key saved",
        "welcome_title": "🤖 DeepSeek Code Assistant",
        "welcome_sub": "🤖 DeepSeek V4 Flash",
        "welcome_hint": "What needs to be done?",
        "diff_title": "✏️ Confirm edit", "diff_old": "⬅️ Old text:", "diff_new": "➡️ New text:",
        "diff_apply": "✅ Apply", "diff_cancel": "❌ Cancel",
        "history_title": "📜 Chat History", "history_empty": "No saved conversations.",
        "history_error": "Cannot read history file.", "history_prazan": "History is empty.",
        "about_title": "💖 About", "about_close": "✕ Close",
        "model_title": "🧠 DeepSeek models", "model_label": "<b>Current models:</b> Add new ones (V5, V6...) here:",
        "model_info": "Format: <b>model_id | Name</b><br>E.g.: <b>deepseek-v5 | DeepSeek V5</b><br>First model is default.",
        "model_add": "➕ Add row", "model_save": "💾 Save", "model_cancel": "✕ Cancel",
        "model_empty": "No valid models!", "model_saved": "✅ Models saved!",
        "key_title": "🔑 API Key", "key_label": "Enter your DeepSeek API key:",
        "key_empty": "API key cannot be empty!",
        "file_confirm": "📄 Create File", "file_confirm_text": "Do you want me to create a new file?",
        "api_missing": "API key not set!",
        "status_model": "🧠 Model: ",
        "create_file_header": "📄 Create File",
    },
    "中文": {
        "flag": "🇨🇳", "open": "📂 打开", "key": "🔑 密钥", "models": "🧠 模型",
        "history": "📜 历史", "new": "🗑️ 新对话",
        "send": "▶ 发送", "thinking": "DeepSeek 思考中...",
        "placeholder": "需要做什么？(按 Enter 发送)",
        "hint": "💡 例如: '显示 main.cpp', '修复错误', '查找 QString'",
        "project": "📁 ", "status_ready": "✅ 就绪", "status_ok": "✅ 已收到回复",
        "status_error": "❌ 错误", "status_cleared": "🗑️ 对话已清除",
        "status_saved": "✅ API密钥已保存",
        "welcome_title": "🤖 DeepSeek 代码助手",
        "welcome_sub": "🤖 DeepSeek V4 Flash",
        "welcome_hint": "需要做什么？",
        "diff_title": "✏️ 确认修改", "diff_old": "⬅️ 旧文本:", "diff_new": "➡️ 新文本:",
        "diff_apply": "✅ 应用", "diff_cancel": "✕ 取消",
        "history_title": "📜 对话历史", "history_empty": "没有保存的对话。",
        "history_error": "无法读取历史文件。", "history_prazan": "历史记录为空。",
        "about_title": "💖 关于", "about_close": "✕ 关闭",
        "model_title": "🧠 DeepSeek 模型", "model_label": "<b>当前模型：</b>在此添加新模型（V5、V6...）：",
        "model_info": "格式：<b>model_id | 名称</b><br>例如：<b>deepseek-v5 | DeepSeek V5</b><br>第一个模型为默认。",
        "model_add": "➕ 添加行", "model_save": "💾 保存", "model_cancel": "✕ 取消",
        "model_empty": "没有有效模型！", "model_saved": "✅ 模型已保存！",
        "key_title": "🔑 API密钥", "key_label": "输入您的DeepSeek API密钥：",
        "key_empty": "API密钥不能为空！",
        "file_confirm": "📄 创建文件", "file_confirm_text": "您要我创建一个新文件吗？",
        "api_missing": "API密钥未设置！",
        "status_model": "🧠 模型: ",
        "create_file_header": "📄 创建文件",
    },
}


def save_language(lang):
    with open(get_data_file(LANG_FILE), "w", encoding="utf-8") as f:
        f.write(lang)


def load_language():
    """Učitava sačuvani jezik."""
    path = get_data_file(LANG_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lang = f.read().strip()
            if lang in LANGUAGES:
                return lang
    return "srpski"


# =============================================================================
# SYSTEM PROMPT
# =============================================================================
SYSTEM_PROMPT = """You are DeepSeek V4 Flash, the latest AI model created by DeepSeek Company (深度求索), China. You are NOT Claude, NOT GPT, NOT any other AI model. You are DeepSeek V4.

You are a coding assistant that helps the user with their C++/Python/Qt project.

CRITICAL: When asked about your identity, you MUST say you are DeepSeek.

IMPORTANT: When the user asks you to create, edit, read, search, list files or run commands - you MUST use the appropriate tool. Do NOT just describe what you would do - actually do it using the tools provided.

You have access to these tools:
- read_file: Read a file
- create_file: Create a new file
- edit_file: Edit an existing file
- list_files: List project files
- search_text: Search in files
- run_command: Run terminal commands
- get_issues: Get build issues

IMPORTANT: Do ONE thing and then reply. Do not read after create, do not delete after edit, do not run dir/del unless asked.

Example flow:
User: "kreiraj fajl test.txt sa tekstom zdravo"
You: call create_file("test.txt", "zdravo") → then reply "Gotovo!" ← STOP, no more tools
"""
