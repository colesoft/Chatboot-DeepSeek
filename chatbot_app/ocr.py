# -*- coding: utf-8 -*-
"""
chatbot_app/ocr.py - Lokalno izvlačenje teksta iz slika (OCR)
================================================================

DeepSeek API prihvata SAMO tekst (vraća 400 "unknown variant `image_url`"
za slike), zato slike obrađujemo LOKALNO, na korisnikovom računaru:

  1. Windows ugrađeni OCR engine (winsdk / winrt)  -> pip install winsdk
     (koristi Windows.Media.Ocr - nema eksternih binarnih fajlova,
      radi na Windows 10/11 bez admin prava)
  2. pytesseract (ako je instaliran zajedno sa Tesseract-om)

Sve funkcije su čiste (bez Qt zavisnosti) i thread-safe - mogu se
pozivati iz pozadinskog thread-a.
"""
import asyncio
import base64
import logging

log = logging.getLogger("chatbot_app.ocr")

# ---------------------------------------------------------------------------
# Detekcija dostupnog OCR engine-a (uradi se jednom, kešira se)
# ---------------------------------------------------------------------------
_WIN_ENGINE = None  # None = nije proveravano, "" = nema, "winsdk"/"winrt" = ima


def _detect_win_ocr():
    """Da li je dostupan Windows OCR (winsdk ili winrt paket)?"""
    global _WIN_ENGINE
    if _WIN_ENGINE is not None:
        return _WIN_ENGINE
    for pkg in ("winsdk", "winrt"):
        try:
            if pkg == "winsdk":
                import winsdk.windows.media.ocr  # noqa: F401
            else:
                import winrt.windows.media.ocr  # noqa: F401
            _WIN_ENGINE = pkg
            return _WIN_ENGINE
        except Exception:
            continue
    _WIN_ENGINE = ""
    return _WIN_ENGINE


def _has_pytesseract():
    try:
        import pytesseract  # noqa: F401
        return True
    except Exception:
        return False


def ocr_available():
    """Da li postoji BILO koji OCR engine? (za UI poruke)"""
    return bool(_detect_win_ocr()) or _has_pytesseract()


def ocr_engine_name():
    """Ime dostupnog engine-a (za prikaz korisniku) ili None."""
    if _detect_win_ocr():
        return "Windows OCR"
    if _has_pytesseract():
        return "Tesseract"
    return None


# ---------------------------------------------------------------------------
# Windows OCR (asinhrono)
# ---------------------------------------------------------------------------
async def _win_ocr_async(img_bytes):
    """Pokreće Windows.Media.Ocr na bajtovima slike. Vraća tekst ili None."""
    engine_name = _detect_win_ocr()
    if engine_name == "winsdk":
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import (
            InMemoryRandomAccessStream, DataWriter,
        )
        from winsdk.windows.globalization import Language
    elif engine_name == "winrt":
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import (
            InMemoryRandomAccessStream, DataWriter,
        )
        from winrt.windows.globalization import Language
    else:
        return None

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(img_bytes)
    await writer.store_async()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        engine = OcrEngine.try_create_from_language(Language("en-US"))
    if engine is None:
        log.warning("Windows OCR engine nije dostupan (nema jezičkih paketa?)")
        return None

    result = await engine.recognize_async(bitmap)
    text = (result.text or "").strip()
    return text or None


# ---------------------------------------------------------------------------
# Tesseract fallback
# ---------------------------------------------------------------------------
def _tesseract_ocr(img_bytes):
    """Fallback na pytesseract (ako korisnik ima Tesseract instaliran)."""
    import io
    from PIL import Image
    import pytesseract

    pil_img = Image.open(io.BytesIO(img_bytes))
    text = pytesseract.image_to_string(pil_img)
    return text.strip() or None


# ---------------------------------------------------------------------------
# Javni API
# ---------------------------------------------------------------------------
def extract_text_from_bytes(img_bytes):
    """Proba sve OCR engine-e redom.

    Vraća (text, engine_name) ili (None, None) ako nijedan nije uspeo.
    """
    if not img_bytes:
        return None, None

    # 1) Windows ugrađeni OCR (najbrži, bez eksternih fajlova)
    if _detect_win_ocr():
        try:
            text = asyncio.run(_win_ocr_async(img_bytes))
            if text:
                return text, "Windows OCR"
        except Exception as e:
            log.warning("Windows OCR greška: %s", e)

    # 2) pytesseract (fallback)
    if _has_pytesseract():
        try:
            text = _tesseract_ocr(img_bytes)
            if text:
                return text, "Tesseract"
        except Exception as e:
            log.warning("Tesseract greška: %s", e)

    return None, None


def extract_text_from_file(path):
    """OCR-uje sliku sa diska. Vraća (text, engine_name) ili (None, None)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return extract_text_from_bytes(data)
    except Exception as e:
        log.warning("Greška pri čitanju slike %s: %s", path, e)
        return None, None


def ocr_data_url_to_text(data_url):
    """OCR-uje image_url data URL (npr. iz runtime API fallback-a).

    Vraća (text, engine_name) ili (None, None).
    """
    if isinstance(data_url, str) and data_url.startswith("data:"):
        _, _, b64part = data_url.partition(",")
        try:
            img_bytes = base64.b64decode(b64part)
            return extract_text_from_bytes(img_bytes)
        except Exception as e:
            log.warning("base64 decode greška: %s", e)
    return None, None
