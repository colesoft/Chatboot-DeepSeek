# -*- coding: utf-8 -*-
"""
vision.py - Slanje slika modelu (image_url / data URL)
=======================================================
DeepSeek chat/completions prihvata slike kao deo `content` liste:

    {"type": "text", "text": "Šta je na slici?"}
    {"type": "image_url",
     "image_url": {"url": "https://.../slika.png", "detail": "high"}}

`url` može biti:
  * javni http(s) URL  -> model sam skida sliku (najbrže, nema base64)
  * data URL           -> "data:image/png;base64,...." (lokalni fajl)

`detail` ("auto" | "low" | "high") kontroliše koliko tokena se troši na sliku:
  low  ~85 tokena   (grubi pregled, grafike, skice)
  high ~detaljno    (tekst na slici, sitni detalji)

Ovaj modul je čist Python (bez PyQt) - lako se testira.
"""

import base64
import mimetypes
import os

# Ograničenja DeepSeek API-ja
MAX_IMAGE_BYTES = 32 * 1024 * 1024   # 32 MiB po slici
MAX_URL_LENGTH = 8192                # dužina image_url stringa
DETAIL_LEVELS = ("auto", "low", "high")

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


class ImageError(Exception):
    """Greška pri pripremi slike za slanje."""


# ---------------------------------------------------------------------------
# Prepoznavanje
# ---------------------------------------------------------------------------
def is_image_url(source):
    """Da li je izvor javni http(s) URL (a ne lokalna putanja)?"""
    if not source:
        return False
    s = str(source).strip().lower()
    return s.startswith("http://") or s.startswith("https://")


def is_data_url(source):
    s = str(source or "").strip().lower()
    return s.startswith("data:image/")


def is_image_source(source):
    """Da li string izgleda kao slika (URL, data URL ili lokalni fajl)?"""
    if not source:
        return False
    if is_image_url(source) or is_data_url(source):
        return True
    try:
        return os.path.isfile(source) and \
            os.path.splitext(source)[1].lower() in IMAGE_EXTS
    except Exception:
        return False


def mime_for(path):
    """MIME tip na osnovu ekstenzije (fallback image/png)."""
    ext = os.path.splitext(str(path))[1].lower()
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    if ext in mapping:
        return mapping[ext]
    guess, _ = mimetypes.guess_type(str(path))
    return guess if guess and guess.startswith("image/") else "image/png"


def label_for(source):
    """Kratko ime za UI/log (bez base64 sadržaja)."""
    s = str(source or "")
    if is_data_url(s):
        return "data-url"
    if is_image_url(s):
        name = s.split("?")[0].rstrip("/").split("/")[-1]
        return name or s[:60]
    return os.path.basename(s) or s


# ---------------------------------------------------------------------------
# Priprema URL-a
# ---------------------------------------------------------------------------
def to_data_url(path):
    """Lokalni fajl -> data URL (base64). Diže ImageError ako je prevelika."""
    if not os.path.isfile(path):
        raise ImageError(f"Slika ne postoji: {label_for(path)}")
    size = os.path.getsize(path)
    if size == 0:
        raise ImageError(f"Slika je prazna: {label_for(path)}")
    if size > MAX_IMAGE_BYTES:
        raise ImageError(
            f"Slika je prevelika ({size / 1048576:.1f} MB, max "
            f"{MAX_IMAGE_BYTES // 1048576} MB): {label_for(path)}")
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
    except OSError as e:
        raise ImageError(f"Ne mogu da pročitam sliku {label_for(path)}: {e}")
    return f"data:{mime_for(path)};base64,{b64}"


def resolve_url(source):
    """Vraća url spreman za payload (http(s) ostaje, lokalni -> data URL)."""
    s = str(source or "").strip()
    if not s:
        raise ImageError("Prazan izvor slike.")
    if is_data_url(s):
        url = s
    elif is_image_url(s):
        if len(s) > MAX_URL_LENGTH:
            raise ImageError(
                f"URL slike je predugačak ({len(s)} > {MAX_URL_LENGTH}): "
                f"{label_for(s)}")
        return s
    else:
        url = to_data_url(s)
    if len(url) > MAX_IMAGE_BYTES * 2:   # ~32MiB sirovo -> ~43MB base64
        raise ImageError(f"Slika je prevelika za slanje: {label_for(s)}")
    return url


def build_image_part(source, detail="auto"):
    """Jedan `image_url` deo za content listu."""
    d = str(detail or "auto").lower()
    if d not in DETAIL_LEVELS:
        d = "auto"
    return {
        "type": "image_url",
        "image_url": {"url": resolve_url(source), "detail": d},
    }


def build_user_content(text, images=None, detail="auto"):
    """Tekst -> string; tekst + slike -> lista delova za content.

    `images` može biti lista putanja/URL-ova ili (putanja, opis) tuple-ova.
    """
    images = images or []
    if not images:
        return text

    parts = []
    if text:
        parts.append({"type": "text", "text": text})

    errors = []
    for item in images:
        if isinstance(item, (tuple, list)):
            src, d = item[0], (item[1] if len(item) > 1 else detail)
        else:
            src, d = item, detail
        try:
            parts.append(build_image_part(src, d))
        except ImageError as e:
            errors.append(str(e))

    if not parts or all(p.get("type") == "image_url" for p in parts):
        # nema teksta i nijedna slika nije prošla
        if not parts:
            raise ImageError("; ".join(errors) or "Nema ispravnih slika.")
    return parts


def count_images(content):
    """Koliko image_url delova ima u content-u (str ili lista)."""
    if not isinstance(content, list):
        return 0
    return sum(1 for p in content
               if isinstance(p, dict) and p.get("type") == "image_url")


def strip_images(content):
    """Ukloni image_url delove; vraća (novi_content, broj_uklonjenih)."""
    if not isinstance(content, list):
        return content, 0
    kept, removed = [], 0
    for p in content:
        if isinstance(p, dict) and p.get("type") == "image_url":
            removed += 1
        else:
            kept.append(p)
    if removed == 0:
        return content, 0
    texts = [p.get("text", "") for p in kept if isinstance(p, dict)]
    if len(kept) == 1 and kept[0].get("type") == "text":
        return texts[0], removed
    return kept, removed
