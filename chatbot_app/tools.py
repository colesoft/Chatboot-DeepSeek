# -*- coding: utf-8 -*-
"""
tools.py - ToolExecutor + tool definicije
===========================================
Definicije alata (JSON šeme) koje se šalju DeepSeek API-ju,
i klasa ToolExecutor koja ih izvršava u projektnom folderu.
"""

import os
import glob
import json
import shutil
import subprocess
import traceback

from .utils import is_within_project
from .logger import log

# 🌐 Web alati (novi /v1/tools/search i /v1/tools/fetch endpointi)
try:
    from .api_tools import (
        TOOL_SCHEMAS as _WEB_SCHEMAS,
        run_tool as _run_web_tool,
    )
except Exception as _e:  # pragma: no cover - api_tools bi trebalo da postoji
    _WEB_SCHEMAS = []
    _run_web_tool = None
    log(f"⚠️ Web alati nedostupni: {_e}")

try:
    from . import config as _cfg
    WEB_SEARCH_ENABLED = getattr(_cfg, "WEB_SEARCH_ENABLED", True)
    WEB_FETCH_ENABLED = getattr(_cfg, "WEB_FETCH_ENABLED", True)
    WEB_SEARCH_COUNT = getattr(_cfg, "WEB_SEARCH_COUNT", 10)
except Exception:
    WEB_SEARCH_ENABLED = True
    WEB_FETCH_ENABLED = True
    WEB_SEARCH_COUNT = 10

# =============================================================================
# DEFINICIJA ALATA (TOOLS) ZA DEEPSEEK API
# =============================================================================

TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all source files in the project (cpp, h, hpp, py, qml, pro, txt, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Optional file pattern filter, e.g. '*.cpp', '*.h', '*.py'",
                        "default": "*.*"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the project. Shows line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path relative to project root, e.g. 'main.cpp' or 'src/utils.h'"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a NEW file in the project with the given content. The user must confirm. File must be within project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path relative to project root, e.g. 'src/newfile.cpp'"
                    },
                    "content": {
                        "type": "string",
                        "description": "Full content of the file to create"
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit an existing file by replacing specific text with new content. The user must confirm each edit. Shows a diff preview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path relative to project root"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "The exact text to find and replace (at least 3-5 lines for context)"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "The new text to replace with"
                    }
                },
                "required": ["filepath", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "Search for text in project files (grep-like). Returns matching lines with file paths and line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for (case-insensitive)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Optional file filter, e.g. '*.cpp', '*.h'",
                        "default": "*.*"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_log",
            "description": "Read Qt Creator build output or issue log. Checks common build directories for log/output files.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a terminal command in the project directory. Shows output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute, e.g. 'qmake', 'cmake --build .', 'python -m pytest'"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_issues",
            "description": "Get a summary of build issues by reading Qt Creator compile_output or build log files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "build_dir": {
                        "type": "string",
                        "description": "Optional build directory path relative to project root. If empty, auto-detect."
                    }
                }
            }
        }
    }
]


def _filtered_web_schemas():
    """Web šeme poštuju korisnikova podešavanja (uključeno/isključeno)."""
    allowed = set()
    if WEB_SEARCH_ENABLED:
        allowed.add("web_search")
    if WEB_FETCH_ENABLED:
        allowed.add("web_fetch")
    return [s for s in _WEB_SCHEMAS
            if s.get("function", {}).get("name") in allowed]


# 🌐 Dodaj web alate u glavnu listu (samo ako su dostupni i uključeni)
TOOLS_DEFINITIONS.extend(_filtered_web_schemas())

_WEB_TOOL_NAMES = ("web_search", "web_fetch")


def refresh_web_tools():
    """Ponovo izračuna TOOLS_DEFINITIONS prema settings.json (bez restarta).

    Menja listu IN-PLACE da bi reference (deepseek_chatbot.TOOLS_DEFINITIONS)
    ostale važeće.
    """
    global WEB_SEARCH_ENABLED, WEB_FETCH_ENABLED, WEB_SEARCH_COUNT
    try:
        _s = _cfg.load_settings()
        WEB_SEARCH_ENABLED = bool(_s.get("web_search_enabled", True))
        WEB_FETCH_ENABLED = bool(_s.get("web_fetch_enabled", True))
        WEB_SEARCH_COUNT = int(_s.get("web_search_count", 10) or 10)
    except Exception as e:
        log(f"⚠️ refresh_web_tools: {e}")
    base = [t for t in TOOLS_DEFINITIONS
            if t.get("function", {}).get("name") not in _WEB_TOOL_NAMES]
    base.extend(_filtered_web_schemas())
    TOOLS_DEFINITIONS[:] = base
    log(f"🌐 Web alati: search={WEB_SEARCH_ENABLED}, "
        f"fetch={WEB_FETCH_ENABLED}, count={WEB_SEARCH_COUNT}")
    return [t["function"]["name"] for t in TOOLS_DEFINITIONS]



# =============================================================================
# IZVRSILAC ALATA (TOOL EXECUTOR)
# =============================================================================

class ToolExecutor:
    """Izvršava alate pozvane od strane AI modela."""

    def __init__(self, project_path, parent_window=None):
        self.project_path = project_path
        self.parent = parent_window  # ChatWindow, za dijaloge potvrde

    # ---- list_files ----
    def list_files(self, pattern="*.*"):
        """Vraća listu fajlova u projektu."""
        results = []
        search_pattern = os.path.join(self.project_path, "**", pattern)
        files = glob.glob(search_pattern, recursive=True)
        # Ignoriši build i .git direktorijume
        ignore_dirs = {"build", ".git", "__pycache__", ".venv", "venv", "node_modules", ".qtcreator"}
        for f in sorted(files):
            if os.path.isfile(f):
                rel = os.path.relpath(f, self.project_path)
                parts = rel.replace("\\", "/").split("/")
                if not any(p in ignore_dirs for p in parts):
                    size = os.path.getsize(f)
                    results.append(f"{rel} ({size} bytes)")
        if not results:
            return "No files found matching pattern: " + pattern
        return "Project files:\n" + "\n".join(results)

    # ---- read_file ----
    def read_file(self, filepath):
        """Čita fajl i vraća sadržaj sa brojevima linija."""
        full_path = os.path.join(self.project_path, filepath)
        if not os.path.isfile(full_path):
            # Probaj kao apsolutnu putanju
            if os.path.isfile(filepath):
                full_path = filepath
            else:
                return f"Error: File not found: {filepath}"

        if not is_within_project(full_path, self.project_path):
            return f"Error: File is outside the project directory: {full_path}"

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            # Ograniči prikaz na 2000 linija
            max_lines = 2000
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                result = f"Showing first {max_lines} lines of {len(lines)}:\n"
            else:
                result = ""

            # Dodaj brojeve linija
            line_width = len(str(len(lines)))
            for i, line in enumerate(lines, 1):
                result += f"{i:>{line_width}}| {line}"

            return result
        except Exception as e:
            return f"Error reading file {filepath}: {str(e)}"

    # ---- create_file ----
    def create_file(self, filepath, content):
        """Kreira novi fajl - traži potvrdu od korisnika."""
        full_path = os.path.join(self.project_path, filepath)

        if not is_within_project(full_path, self.project_path):
            return f"Error: File would be outside project directory: {full_path}"

        if os.path.exists(full_path):
            return f"Error: File already exists: {filepath}. Use edit_file to modify existing files."

        # Pitaj korisnika za potvrdu
        if self.parent:
            ok = self.parent._confirm_create_file(filepath, content)
            if not ok:
                return "User cancelled: file creation was rejected."

        # Napravi direktorijum ako ne postoji
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ File created successfully: {filepath} ({len(content)} bytes)"
        except Exception as e:
            return f"Error creating file: {str(e)}"

    # ---- edit_file ----
    def edit_file(self, filepath, old_text, new_text):
        """Menja deo fajla - traži potvrdu od korisnika."""
        full_path = os.path.join(self.project_path, filepath)

        if not is_within_project(full_path, self.project_path):
            return f"Error: File is outside project directory: {full_path}"

        if not os.path.isfile(full_path):
            return f"Error: File not found: {filepath}"

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file for edit: {str(e)}"

        if old_text not in content:
            return f"Error: Could not find the specified text in {filepath}. The text to replace must match exactly."

        # Pitaj korisnika za potvrdu
        if self.parent:
            ok = self.parent._confirm_edit_file(filepath, old_text, new_text)
            if not ok:
                return "User cancelled: edit was rejected."

        # Napravi backup
        backup_path = full_path + ".bak"
        try:
            shutil.copy2(full_path, backup_path)
        except:
            pass

        try:
            new_content = content.replace(old_text, new_text, 1)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"✅ File edited successfully: {filepath}\nBackup saved: {filepath}.bak"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    # ---- search_text ----
    def search_text(self, query, file_pattern="*.*"):
        """Pretražuje tekst u fajlovima projekta."""
        results = []
        search_pattern = os.path.join(self.project_path, "**", file_pattern)
        files = glob.glob(search_pattern, recursive=True)
        ignore_dirs = {"build", ".git", "__pycache__", ".venv", "venv", "node_modules", ".qtcreator"}

        query_lower = query.lower()

        for f in sorted(files):
            if not os.path.isfile(f):
                continue
            rel = os.path.relpath(f, self.project_path)
            parts = rel.replace("\\", "/").split("/")
            if any(p in ignore_dirs for p in parts):
                continue

            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        if query_lower in line.lower():
                            results.append(f"{rel}:{i}: {line.rstrip()[:200]}")
            except:
                continue

        if not results:
            return f"No matches found for: {query}"

        # Ograniči broj rezultata
        max_results = 200
        if len(results) > max_results:
            results = results[:max_results]
            summary = f"Found {len(results)}+ matches. Showing first {max_results}:\n\n"
        else:
            summary = f"Found {len(results)} matches:\n\n"

        return summary + "\n".join(results)

    # ---- read_log ----
    def read_log(self):
        """Čita build logove iz Qt Creator build direktorijuma."""
        log_dirs = [
            os.path.join(self.project_path, "build"),
        ]

        # Potrazi sve build direktorijume
        for item in glob.glob(os.path.join(self.project_path, "build*")):
            if os.path.isdir(item):
                log_dirs.append(item)

        logs = []

        # Potrazi compile_output.log ili slično
        for d in log_dirs:
            if os.path.isdir(d):
                for root, dirs, files in os.walk(d):
                    for f in files:
                        if any(x in f.lower() for x in ["compile_output", "build_log", "output", "make_output", "ninja_output"]):
                            fp = os.path.join(root, f)
                            try:
                                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                    content = fh.read()
                                rel = os.path.relpath(fp, self.project_path)
                                if len(content) > 10000:
                                    # Prikaži poslednjih 10000 karaktera
                                    content = "... (truncated) ...\n" + content[-10000:]
                                logs.append(f"=== {rel} ===\n{content}")
                            except:
                                continue

        if logs:
            return "\n\n".join(logs)
        else:
            return "No build log files found. Try running a build first (run_command: qmake or cmake --build .)"

    # ---- run_command ----
    def run_command(self, command):
        """Izvršava komandu u projektnom direktorijumu."""
        log(f"⚡ run_command: {command[:100]}")
        t0 = __import__('time').time()
        try:
            # ⚠️ VAŽNO: ne koristimo text=True jer na Windows-u (cp1250)
            # ne može da dekodira binarni output (npr. byte 0x90).
            # Umesto toga čitamo binarno i dekodiramo sa errors='replace'
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                timeout=60  # Timeout od 60s
            )
            # Dekodiraj sa 'replace' da izbegnemo UnicodeDecodeError
            stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
            output = ""
            if stdout:
                output += stdout
            if stderr:
                if output:
                    output += "\n--- stderr ---\n"
                output += stderr
            if result.returncode != 0:
                output += f"\n❌ Command exited with code {result.returncode}"
            else:
                output += f"\n✅ Command completed successfully (exit code 0)"

            # Ograniči output
            if len(output) > 15000:
                output = output[:15000] + "\n... (output truncated) ..."

            log(f"⚡ run_command KRAJ ({(__import__('time').time()-t0)*1000:.0f} ms, exit {result.returncode})")
            return output if output else "(no output)"
        except subprocess.TimeoutExpired:
            log(f"⚡ run_command TIMEOUT (>60s): {command[:100]}")
            return "❌ Command timed out after 60 seconds"
        except Exception as e:
            log(f"⚡ run_command GRESKA: {e}")
            return f"❌ Error running command: {str(e)}"

    # ---- get_issues ----
    def get_issues(self, build_dir=""):
        """Čita build greške iz Qt Creator-a."""
        if build_dir:
            search_dirs = [os.path.join(self.project_path, build_dir)]
        else:
            search_dirs = [os.path.join(self.project_path, "build")]

        for d in search_dirs:
            if os.path.isdir(d):
                break
        else:
            # Potrazi .qtcreator direktorijum
            qtcreator_dir = os.path.join(self.project_path, ".qtcreator")
            issues_file = os.path.join(qtcreator_dir, "issues.xml")
            if os.path.isfile(issues_file):
                try:
                    with open(issues_file, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()
                except:
                    pass

            # Potrazi compile_commands.json
            for root, dirs, files in os.walk(self.project_path):
                if "compile_commands.json" in files:
                    fp = os.path.join(root, "compile_commands.json")
                    try:
                        with open(fp, "r", encoding="utf-8", errors="replace") as f:
                            data = json.load(f)
                        entries = [os.path.basename(e.get("file", "")) for e in data[:50]]
                        return f"Found compile_commands.json with {len(data)} entries.\nFiles: {', '.join(entries)}"
                    except:
                        continue

            return "Could not find build issues. Try running build first with: run_command('qmake && make') or run_command('cmake --build .')"

    # ---- web_search ----
    def web_search(self, query, count=None, need_content=False,
                   ori_question=None):
        """🌐 Web pretraga preko DeepSeek /v1/tools/search."""
        if not WEB_SEARCH_ENABLED:
            return "❌ Web pretraga je isključena u podešavanjima."
        if _run_web_tool is None:
            return "❌ Web alati nisu dostupni (api_tools.py nije učitan)."
        if not query or not str(query).strip():
            return "❌ web_search: 'query' je obavezan."

        api_key = self._api_key()
        if not api_key:
            return "❌ web_search: API ključ nije postavljen."

        try:
            cnt = int(count if count is not None else WEB_SEARCH_COUNT)
        except (TypeError, ValueError):
            cnt = WEB_SEARCH_COUNT
        cnt = max(1, min(50, cnt))   # API dozvoljava 1-50

        log(f"🌐 web_search: {str(query)[:120]} (count={cnt})")
        ok, out = _run_web_tool(
            "web_search",
            {"query": query, "count": cnt,
             "need_content": bool(need_content),
             "ori_question": ori_question},
            api_key,
        )
        if not ok:
            log(f"🌐 web_search GREŠKA: {out[:200]}")
        return out

    # ---- web_fetch ----
    def web_fetch(self, url):
        """🌐 Dohvati sadržaj stranice preko DeepSeek /v1/tools/fetch."""
        if not WEB_FETCH_ENABLED:
            return "❌ Web fetch je isključen u podešavanjima."
        if _run_web_tool is None:
            return "❌ Web alati nisu dostupni (api_tools.py nije učitan)."
        u = str(url or "").strip()
        if not u.lower().startswith(("http://", "https://")):
            return "❌ web_fetch: 'url' mora počinjati sa http:// ili https://"

        api_key = self._api_key()
        if not api_key:
            return "❌ web_fetch: API ključ nije postavljen."

        log(f"🌐 web_fetch: {u[:120]}")
        ok, out = _run_web_tool("web_fetch", {"url": u}, api_key)
        if not ok:
            log(f"🌐 web_fetch GREŠKA: {out[:200]}")
        return out

    def _api_key(self):
        """API ključ iz parent window-a ili iz fajla."""
        key = getattr(self.parent, "api_key", None) if self.parent else None
        if key:
            return key
        try:
            from .utils import load_api_key
            return load_api_key()
        except Exception:
            return ""

    # ---- dispatch ----
    def dispatch(self, tool_name, arguments):
        """Prosledjuje poziv odgovarajućoj metodi."""
        method_map = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "create_file": self.create_file,
            "edit_file": self.edit_file,
            "search_text": self.search_text,
            "read_log": self.read_log,
            "run_command": self.run_command,
            "get_issues": self.get_issues,
            "web_search": self.web_search,
            "web_fetch": self.web_fetch,
        }
        func = method_map.get(tool_name)
        if not func:
            return f"Error: Unknown tool '{tool_name}'"

        try:
            if isinstance(arguments, str):
                args = json.loads(arguments)
            else:
                args = arguments
            # ⚠️ Ako arguments nije dict (npr. null), func(**args) baca TypeError -
            # uhvaćeno ispod. Ali ako funkcija vrati None, pretvori u string.
            result = func(**args)
            if result is None:
                result = "(no output)"
            return result
        except TypeError as e:
            return f"Error: Invalid arguments for {tool_name}: {str(e)}\nExpected arguments: {TOOLS_DEFINITIONS}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}\n{traceback.format_exc()}"
