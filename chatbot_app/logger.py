# -*- coding: utf-8 -*-
"""
logger.py - Jednostavan logger za debug zamrzavanja
=====================================================
Piše u app_log.txt u data folderu sa vremenskim oznakama.

Korišćenje:
    from .logger import log, log_time
    log("API poziv kreće")
    with log_time("save_history"):
        ...
"""

import os
import sys
import time
import threading
import traceback
from datetime import datetime

from .config import get_data_file

_LOG_FILE = None
_DEBUG = True
_MAX_LOG_BYTES = 5 * 1024 * 1024   # 5 MB - posle ovoga se log rotira


def _get_log_path():
    global _LOG_FILE
    if _LOG_FILE is None:
        _LOG_FILE = get_data_file("app_log.txt")
    return _LOG_FILE


def _rotate_if_big(path):
    """Ako je log veći od _MAX_LOG_BYTES, prebaci ga u *.old (max 1 stari)."""
    try:
        if os.path.exists(path) and os.path.getsize(path) > _MAX_LOG_BYTES:
            old = path[:-4] + ".old.txt" if path.endswith(".txt") else path + ".old"
            if os.path.exists(old):
                os.remove(old)
            os.replace(path, old)
    except Exception:
        pass


def log(msg):
    """Upisuje poruku u log fajl sa vremenskom oznakom."""
    if not _DEBUG:
        return
    try:
        path = _get_log_path()
        _rotate_if_big(path)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


# =============================================================================
# 💥 CRASH LOGGER - hvata neuhvaćene izuzetke (PyQt5 kod njih ABORTUJE aplikaciju!)
# =============================================================================
def _write_crash(title, tb_text):
    """Upisuje traceback u crash_log.txt (i u app_log.txt) i na stderr."""
    try:
        path = get_data_file("crash_log.txt")
        _rotate_if_big(path)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"[{ts}] {title}\n")
            f.write("=" * 70 + "\n")
            f.write(tb_text.rstrip() + "\n")
    except Exception:
        pass
    try:
        sys.stderr.write(f"\n💥 {title}\n{tb_text}\n")
        sys.stderr.flush()
    except Exception:
        pass
    log(f"💥 CRASH: {title} (vidi crash_log.txt)")


def install_crash_handlers():
    """Instalira globalne hvatаče izuzetaka.

    ⚠️ VAŽNO: neuhvaćen izuzetak u Qt slotu (npr. returnPressed -> _send_message)
    u PyQt5 izaziva qFatal() -> aplikacija se ruši BEZ ikakve poruke.
    Ovim hook-om dobijamo traceback u crash_log.txt.
    """
    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _write_crash(f"Neuhvaćen izuzetak: {exc_type.__name__}: {exc_value}", tb_text)

    sys.excepthook = _excepthook

    # Python 3.8+: izuzeci iz niti (threading)
    if hasattr(threading, "excepthook"):
        def _thread_hook(args):
            tb_text = "".join(traceback.format_exception(
                args.exc_type, args.exc_value, args.exc_traceback))
            _write_crash(
                f"Izuzetak u niti '{args.thread.name if args.thread else '?'}': "
                f"{args.exc_type.__name__}: {args.exc_value}", tb_text)
        threading.excepthook = _thread_hook

    log("🛡️ Crash handler instaliran (crash_log.txt)")


def log_time(label):
    """Kontekst menadžer koji meri koliko traje blok koda.

    Primer:
        with log_time("save_history"):
            self._save_history()
    """
    class _Timer:
        def __enter__(self):
            self.t0 = time.time()
            log(f"⏱️ START: {label}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed_ms = (time.time() - self.t0) * 1000
            if exc_type:
                log(f"⏱️ ERROR: {label} ({elapsed_ms:.0f} ms) - {exc_val}")
            else:
                log(f"⏱️ END:   {label} ({elapsed_ms:.0f} ms)")
            return False  # ne guta izuzetke

    return _Timer()
