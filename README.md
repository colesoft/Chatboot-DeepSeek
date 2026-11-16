# 🤖 DeepSeek Code Assistant

> **🇷🇸 Pametni AI asistent za tvoj programerski projekat**  
> **🇬🇧 Smart AI assistant for your coding project**  
> **🇨🇳 智能AI编程助手，助力你的项目开发**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green?logo=qt)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](#)
[![DeepSeek](https://img.shields.io/badge/Powered%20by-DeepSeek-4A90D9?logo=deepseek)](https://deepseek.com)

---

## 📥 Instalacija / Install / 安装

> **Windows 10/11** · potreban samo Python 3.8+ (skripta ga sama instalira ako ga nema)

### 1️⃣ Skini projekat / Download the project

**Opcija A — ZIP (najlakše, bez git-a):**

👉 **[⬇️ Download ZIP](https://github.com/colesoft/Chatboot-DeepSeek/archive/refs/heads/main.zip)**

Raspakuj u npr. `C:\DeepSeekAssistant\`

**Opcija B — git clone:**
```bash
git clone https://github.com/colesoft/Chatboot-DeepSeek.git
cd Chatboot-DeepSeek
```

### 2️⃣ Instaliraj (jedan dvoklik)

Dvoklik na **`INSTALL.bat`** — radi sve sam:

| Korak | Šta radi |
|:--|:--|
| 1 | Nađe Python (`py`/`python`/`python3`, i standardne foldere) |
| 2 | Ako Pythona nema → **ponudi automatsku instalaciju** (winget ili download sa python.org) |
| 3 | Instalira `PyQt5` + `requests` preko `python -m pip` |
| 4 | Napravi precicu **“DeepSeek Code Assistant”** na Desktopu |
| 5 | Pokrene aplikaciju |

> ⚠️ Ako Windows prikaže „Windows protected your PC“ → *More info* → *Run anyway*
> (skripta je `.bat`, nije potpisan sertifikatom).

### 3️⃣ Pokretanje posle instalacije

- 🖱️ Precica **DeepSeek Code Assistant** na Desktopu, ili
- 🖱️ dvoklik na **`DeepSeek Chatbot.vbs`** (bez crnog prozora), ili
- ⌨️ `run.bat` u folderu projekta

### 🔑 Prvi korak u aplikaciji

Otvori ⚙️ **Podešavanja** i unesi svoj **DeepSeek API ključ**
([platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)).

### 🗑️ Deinstalacija

Obriši folder + precicu sa Desktopa. Nigde se ništa ne instalira u registry.

<details>
<summary>🇬🇧 English — Download &amp; Install (click)</summary>

1. **[Download ZIP](https://github.com/colesoft/Chatboot-DeepSeek/archive/refs/heads/main.zip)** and extract, or `git clone https://github.com/colesoft/Chatboot-DeepSeek.git`
2. Double-click **`INSTALL.bat`** — it finds/installs Python, installs `PyQt5`, creates a Desktop shortcut and launches the app.
3. Enter your **DeepSeek API key** in ⚙️ Settings ([platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)).
4. Afterwards: use the Desktop shortcut, `DeepSeek Chatbot.vbs`, or `run.bat`.
5. Uninstall: delete the folder + shortcut. Nothing is written to the registry.

</details>

<details>
<summary>🇨🇳 中文 — 下载与安装（点击展开）</summary>

1. **[下载 ZIP](https://github.com/colesoft/Chatboot-DeepSeek/archive/refs/heads/main.zip)** 并解压，或 `git clone https://github.com/colesoft/Chatboot-DeepSeek.git`
2. 双击 **`INSTALL.bat`** — 自动查找/安装 Python、安装 `PyQt5`、创建桌面快捷方式并启动程序。
3. 在 ⚙️ 设置中填入你的 **DeepSeek API 密钥**（[platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)）。
4. 之后可通过桌面快捷方式、`DeepSeek Chatbot.vbs` 或 `run.bat` 启动。
5. 卸载：删除文件夹和快捷方式即可，不写入注册表。

</details>

---

## 🇷🇸 Srpski

### 📖 Opis
**DeepSeek Code Assistant** je desktop aplikacija koja koristi **DeepSeek AI** za čitanje, kreiranje i izmenu fajlova u tvom programerskom projektu. Dovoljno je da napišeš šta treba uraditi, a AI će to uraditi umesto tebe!

### ✨ Mogućnosti
- 📂 **Čitanje fajlova** — bilo koje ekstenzije (.cpp, .h, .py, .php, .html...)
- 📄 **Kreiranje fajlova** — uz tvoju potvrdu ili automatski
- ✏️ **Izmena fajlova** — sa diff prikazom promena
- 🔍 **Pretraga teksta** — kroz ceo projekat
- ⚡ **Run komande** — build, git, pa i `del` ako zatražiš
- 🛡️ **Auto-apply** — automatsko odobravanje (sa limitom)
- ⛔ **STOP dugme** — prekida AI petlju u svakom trenutku
- 🌐 **Višejezični interfejs** — 🇷🇸 🇬🇧 🇨🇳
- 📜 **History** — automatsko čuvanje i učitavanje sesija
- 💰 **Praćenje troškova** — cena po zahtevu i sesiji, špic/van špica (do −50%), cache hit ušteda; klik na indikator otvara **dijalog detalja** (broj zahteva, ukupno, prosek, ušteda po cache)
- 🖥️ **Bez crne konzole** — konzolni prozor se pri startu automatski skriva; ili pokreni preko `DeepSeek Chatbot.vbs` (potpuno tiho)
- ⚙️ **Podešavanja** — prilagodi sve parametre kroz UI

### 🚀 Pokretanje
```bash
pip install PyQt5
python main.py
```

Ili dvoklik na **`DeepSeek Chatbot.vbs`** — pokreće se bez ikakvog konzolnog prozora.

---

## 🇬🇧 English

### 📖 Description
**DeepSeek Code Assistant** is a desktop application powered by **DeepSeek AI** that reads, creates, and edits files in your programming project. Just describe what needs to be done, and the AI will do it for you!

### ✨ Features
- 📂 **Read files** — any extension (.cpp, .h, .py, .php, .html...)
- 📄 **Create files** — with confirmation or auto-apply mode
- ✏️ **Edit files** — with diff preview
- 🔍 **Search text** — across the entire project
- ⚡ **Run commands** — build, git, or even `del` if you ask
- 🛡️ **Auto-apply** — automatic approval (with limits)
- ⛔ **STOP button** — breaks AI loop at any moment
- 🌐 **Multilingual UI** — 🇷🇸 🇬🇧 🇨🇳
- 📜 **History** — automatic session saving and loading
- 💰 **Cost tracking** — per-request & session price, peak/off-peak (up to −50%), cache-hit savings; click the indicator to open a **details dialog** (request count, total, average, cache savings)
- 🖥️ **No console window** — the console is auto-hidden on startup; or launch via `DeepSeek Chatbot.vbs` (fully silent)
- ⚙️ **Settings** — customize all parameters via UI

### 🚀 How to run
```bash
pip install PyQt5
python main.py
```

Or double-click **`DeepSeek Chatbot.vbs`** — starts with no console window at all.

---

## 🇨🇳 中文

### 📖 简介
**DeepSeek Code Assistant** 是一款由 **DeepSeek AI** 驱动的桌面应用程序，可以读取、创建和编辑你的编程项目文件。只需描述需求，AI 就会帮你完成！

### ✨ 功能特点
- 📂 **读取文件** — 支持任何扩展名（.cpp、.h、.py、.php、.html...）
- 📄 **创建文件** — 手动确认或自动模式
- ✏️ **编辑文件** — 带差异预览
- 🔍 **搜索文本** — 在整个项目中搜索
- ⚡ **运行命令** — 构建、git 或 `del` 等
- 🛡️ **自动应用** — 自动批准（有限制）
- ⛔ **停止按钮** — 随时中断 AI 循环
- 🌐 **多语言界面** — 🇷🇸 🇬🇧 🇨🇳
- 📜 **历史记录** — 自动保存和加载会话
- 💰 **成本追踪** — 每次请求和会话费用、高峰/低谷（最高 −50%）、缓存命中节省；点击指示器打开**详情对话框**（请求数、总额、平均值、缓存节省）
- 🖥️ **无黑色控制台** — 启动时自动隐藏控制台窗口；或使用 `DeepSeek Chatbot.vbs` 启动（完全静默）
- ⚙️ **设置** — 通过界面自定义所有参数

### 🚀 运行方式
```bash
pip install PyQt5
python main.py
```

或双击 **`DeepSeek Chatbot.vbs`** — 完全没有控制台窗口。

---

## 🛡️ Loop Protection / 循环保护

| Level | 🇷🇸 Srpski | 🇬🇧 English | 🇨🇳 中文 |
|:------|:-----------|:------------|:--------|
| 1 | Pattern detekcija | Pattern detection | 模式检测 |
| 2 | Create→Del→Create | Create→Del→Create | 创建→删除→创建 |
| 3 | Max tool calls | Max tool calls | 最大工具调用数 |
| 4 | Max fajlova (auto-apply) | Max files (auto-apply) | 最大文件数 |
| 5 | ⛔ STOP dugme | ⛔ STOP button | ⛔ 停止按钮 |

All limits are adjustable in ⚙️ Settings / 所有限制可在 ⚙️ 设置中调整

---

## ⚙️ Settings / 设置

| Parameter 🇷🇸 | Parameter 🇬🇧 | Default | Options |
|:--------------|:--------------|:--------|:--------|
| Max alata po poruci | Max tool calls | 50 | 20 – 1000 |
| Max fajlova (auto-apply) | Max files | 10 | 5 – 10000 |
| Tokeni pre kompresije | Tokens before compression | 8000 | 1K – 50K |
| Maks context | Max context | 800000 | 100K – 1M |
| Max sesija u istoriji | Max history sessions | 50 | 10 – 100 |
| Poruka posle kompresije | Messages after compression | 10 | 5 – 30 |
| Pattern detekcija | Pattern detection | 50 | 0 – 10000 |

---

## 🔧 Tech / 技术

- **Language:** Python 3.8+
- **GUI:** PyQt5
- **API:** DeepSeek Chat (function calling)
- **Platform:** Windows 10/11

### Project structure / 项目结构
```
├── main.py                  # Entry point (splash + pokretanje) / 入口点
├── deepseek_chatbot.py      # ChatWindow (glavni prozor) / 主窗口
├── chatbot_app/             # Refaktorisani moduli / 模块
│   ├── config.py            # Konfiguracija, putanje, settings / 配置
│   ├── i18n.py              # Prevodi (sr/en/zh), SYSTEM_PROMPT / 翻译
│   ├── utils.py             # Helper funkcije / 工具函数
│   ├── tools.py             # ToolExecutor + alati / 工具执行器
│   ├── api_client.py        # DeepSeek API logika / API 逻辑
│   ├── pricing.py           # Cene, špic/van špica, cache, procena troškova / 价格、高峰/低谷、缓存、成本估算
│   ├── widgets.py           # DiffDialog i widgeti / 对话框
│   ├── history.py           # HistoryMixin (sesije) / 历史记录
│   └── ui/
│       ├── dialogs.py       # DialogsMixin (Settings, Models...) / 对话框
│       ├── project_context.py # ProjectContextMixin / 项目上下文
│       └── theme.py         # QSS stilovi / 样式
├── deepseek.ico              # Icon / 图标
├── requirements.txt          # Dependencies / 依赖
├── INSTALL.bat               # One-click installer / 一键安装
├── run.bat                   # Windows launcher / 启动器
├── DeepSeek Chatbot.vbs      # Silent launcher (no console) / 静默启动器
├── install_deps.bat          # Install dependencies / 安装依赖
├── installer_script.iss      # Inno Setup script
├── README.md                 # This file / 本文件
├── .gitignore
└── LICENSE
```

### 🚀 Pokretanje
```bash
python main.py                # Preporučeno (splash screen + sve)
python deepseek_chatbot.py    # Isto radi (kompatibilnost sa starom komandom)
```

---

## 🖥️ Bez crnog konzolnog prozora / No console window / 无控制台窗口

Na Windows-u `python.exe` je konzolna aplikacija, pa se uz GUI prozor otvara i crni
prozor sa svojom ikonicom u taskbaru. Rešeno na tri načina:

| Način 🇷🇸 | 🇬🇧 | 🇨🇳 | Konzola |
|:----------|:----|:----|:--------|
| Dvoklik na `DeepSeek Chatbot.vbs` | Double-click the `.vbs` | 双击 `.vbs` | ❌ nikad se ne pojavi |
| `python main.py` | same | 同上 | 🙈 skrije se odmah pri startu |
| `DeepSeekAssistant.exe` (PyInstaller) | same | 同上 | ❌ `console=False` |

`main.py` poziva `hide_console()` kao **prvu** stvar u `main()` — pre splasha i pre
bilo kog prozora, tako da nema ni treptaja crnog prozora:

```python
def hide_console():
    if not IS_WINDOWS:
        return
    if os.environ.get("DEEPSEEK_SHOW_CONSOLE", "") == "1":
        return
    import ctypes
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
```

Konzola se **ne gasi, samo skriva** — `stdout` ostaje živ, pa `print()` i
`traceback` rade normalno (a sve ide i u `app_log.txt` / `crash_log.txt`).

### 🔧 Debug: vrati konzolu / Get the console back / 恢复控制台
```bat
set DEEPSEEK_SHOW_CONSOLE=1
python main.py
```
Windows (cmd): `set DEEPSEEK_SHOW_CONSOLE=1` · PowerShell: `$env:DEEPSEEK_SHOW_CONSOLE=1`

> 💡 `DeepSeek Chatbot.vbs` sam pronalazi Python (`py -3` ili `python`) i postavlja
> radni direktorijum, pa radi i ako je `run.bat` obrisan. Za prečicu na Desktop:
> desni klik na fajl → *Send to* → *Desktop (create shortcut)*.

---

## 👨‍💻 Author / 作者 / Autor

**Cole_Soft** — Kruševac, Serbia 🇷🇸  
🌐 [www.colesoft.net](https://www.colesoft.net)

> ❤️ 🇷🇸 Napravljeno sa ljubavlju prema Kini, srpskom narodu i celom svetu!  
> ❤️ 🇬🇧 Made with love for China, the Serbian people, and the whole world!  
> ❤️ 🇨🇳 满怀对中国的热爱、对塞尔维亚人民的热爱、对全世界的热爱而制作！  
> 深圳 · 中国 · 世界

---

## 📜 License / 许可证 / Licenca

MIT License — free to use, modify, and share! 🎉
