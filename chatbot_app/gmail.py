# -*- coding: utf-8 -*-
"""
gmail.py - Provera nepročitanih email-ova (Gmail IMAP)
========================================================
Koristi Gmail IMAP (imap.gmail.com:993) + App Password.

⚠️ VAŽNO: Potreban je **App Password** (16 znakova) iz Google naloga:
Google nalog → Sigurnost → Verifikacija u 2 koraka → App passwords.
Obična lozinka NE radi (Gmail blokira "less secure apps").

Opcioni search upit koristi Gmail web sintaksu (from:, subject:, is:unread...)
preko X-GM-RAW IMAP ekstenzije, sa fallback na standardni UNSEEN search.
"""

import imaplib
import socket

from .logger import log

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
TIMEOUT_SECONDS = 6  # Kratak timeout - ne želimo da čekamo predugo


def get_gmail_unread_count(gmail_user, app_password, search_query=""):
    """Vraća broj nepročitanih email-ova u Gmail Inbox-u.

    Parametri:
        gmail_user      - Gmail adresa (npr. "tvoj.mail@gmail.com")
        app_password    - Google App Password (16 znakova)
        search_query    - Opcioni Gmail stil upit (npr. "from:sef@firma.rs",
                          "subject:izvestaj", "is:unread from:x")

    Povratna vrednost:
        int - broj nepročitanih email-ova (>= 0)
        -1  - greška / Gmail nedostupan / loši parametri
    """
    user = (gmail_user or "").strip()
    pwd = (app_password or "").strip()
    query = (search_query or "").strip()

    if not user or not pwd:
        log("⚠️ Gmail: nedostaje korisničko ime ili app password")
        return -1

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(TIMEOUT_SECONDS)
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(user, pwd)
        mail.select("INBOX", readonly=True)  # readonly - ništa ne menjamo

        data = _search_unread(mail, query)
        if data is None:
            log("⚠️ Gmail: search nije uspeo (loš upit ili server)")
            return -1

        ids = (data[0] or b"").split()
        return len(ids)
    except Exception as e:
        log(f"⚠️ Gmail IMAP greška: {e}")
        return -1
    finally:
        try:
            if mail is not None:
                mail.logout()
        except Exception:
            pass
        socket.setdefaulttimeout(old_timeout)


def _search_unread(mail, query):
    """Vraća IMAP search data (lista UID/seq brojeva) za nepročitane email-ove.

    - Ako je query dat, prvo proba Gmail sintaksu preko X-GM-RAW ekstenzije
      (podržava "from:", "subject:", "is:unread"... kao u Gmail web-u).
    - Ako to ne uspe, pada na standardni IMAP: UNSEEN + TEXT pretragu.
    """
    if query:
        # 1) Gmail web sintaksa preko X-GM-RAW ekstenzije
        try:
            typ, data = mail.search(None, "X-GM-RAW", f'"is:unread {query}"')
            if typ == "OK":
                return data
        except Exception:
            pass
        # 2) Fallback: standardni IMAP UNSEEN + TEXT
        try:
            typ, data = mail.search(None, "UNSEEN", "TEXT", f'"{query}"')
            if typ == "OK":
                return data
        except Exception:
            pass
        return None

    # Bez upita - prost UNSEEN search
    try:
        typ, data = mail.search(None, "UNSEEN")
        if typ == "OK":
            return data
    except Exception:
        pass
    return None
