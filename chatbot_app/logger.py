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
import time
from datetime import datetime

from .config import get_data_file

_LOG_FILE = None
_DEBUG = True


def _get_log_path():
    global _LOG_FILE
    if _LOG_FILE is None:
        _LOG_FILE = get_data_file("app_log.txt")
    return _LOG_FILE


def log(msg):
    """Upisuje poruku u log fajl sa vremenskom oznakom."""
    if not _DEBUG:
        return
    try:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


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
