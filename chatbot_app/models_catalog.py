# -*- coding: utf-8 -*-
"""
models_catalog.py - Katalog modela sa /models endpointa (metapodaci)
=====================================================================
DeepSeek `/models` endpoint od sada vraća BOGATE metapodatke po modelu:

    {
      "id": "deepseek-flash",
      "name": "DeepSeek-V4.1-Flash",
      "context_window": 1048576,
      "max_output_tokens": 393216,
      "input_modalities": ["text", "image"],      <-- VISION!
      "output_modalities": ["text"],
      "effort": {"supported_levels": ["low", "high", "max"],
                 "default_level": "high"}
    }

Ovaj modul te podatke normalizuje i čuva u `models.json` (cache u
AppData folderu), pa aplikacija VIŠE NE MORA da pogađa:
  - koji model podržava slike (vision)  -> input_modalities sadrži "image"
  - koliki je kontekst / max output     -> context_window / max_output_tokens
  - koji reasoning_effort nivoi postoje -> effort.supported_levels

Bez PyQt zavisnosti - može da se testira iz konzole.
"""

import json
import ssl
import urllib.error
import urllib.request

from .config import (
    DEEPSEEK_LIST_MODELS_URL,
    load_models_config,
    save_models_config,
)

# Kada /models ne vrati metapodatke (stari cache), koristimo ove vrednosti.
DEFAULT_CONTEXT_WINDOW = 1048576
DEFAULT_MAX_OUTPUT_TOKENS = 393216

# Nivoi reasoning_effort-a koje DeepSeek prihvata
EFFORT_LEVELS = ("low", "high", "max")
DEFAULT_EFFORT = "high"


class ModelCatalogError(Exception):
    """Greška pri čitanju /models endpointa."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.message = message
        self.status = status

    def __str__(self):
        if self.status:
            return f"[HTTP {self.status}] {self.message}"
        return self.message


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _ssl_context():
    """SSL kontekst sa fallback-om (Windows 'nested asn1 error')."""
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def fetch_models_raw(api_key, timeout=30):
    """GET /models -> lista sirovih dict-ova."""
    if not api_key:
        raise ModelCatalogError("API ključ nije postavljen.", status=401)

    req = urllib.request.Request(
        DEEPSEEK_LIST_MODELS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=_ssl_context()) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        msg = f"HTTP greška {e.code} pri čitanju liste modela."
        if e.code == 401:
            msg = "Neispravan API ključ."
        elif e.code == 402:
            msg = "Nema dovoljno kredita na nalogu."
        raise ModelCatalogError(msg, status=e.code)
    except urllib.error.URLError as e:
        raise ModelCatalogError(f"Nema veze sa api.deepseek.com: {e.reason}")
    except Exception as e:
        raise ModelCatalogError(f"Greška pri čitanju modela: {e}")

    try:
        data = json.loads(raw)
    except Exception:
        raise ModelCatalogError("Odgovor /models nije ispravan JSON.")

    models = data.get("data") if isinstance(data, dict) else data
    if not isinstance(models, list):
        raise ModelCatalogError("Odgovor /models nema listu modela.")
    return models


# ---------------------------------------------------------------------------
# NORMALIZACIJA
# ---------------------------------------------------------------------------
def normalize_model(raw, default=False):
    """Pretvara sirov model sa API-ja u naš format (models.json)."""
    if not isinstance(raw, dict):
        return None
    mid = raw.get("id")
    if not mid:
        return None

    modalities = raw.get("input_modalities") or ["text"]
    if isinstance(modalities, str):
        modalities = [modalities]
    modalities = [str(m).lower() for m in modalities]

    effort = raw.get("effort") or {}
    levels = effort.get("supported_levels") or []
    if isinstance(levels, str):
        levels = [levels]
    levels = [str(x).lower() for x in levels if str(x).lower() in EFFORT_LEVELS]
    default_effort = effort.get("default_level")
    if default_effort not in levels:
        default_effort = levels[0] if levels else None

    return {
        "id": mid,
        "name": raw.get("name") or mid,
        "default": bool(default),
        # 👁️ vision = model prima slike
        "vision": "image" in modalities,
        "input_modalities": modalities,
        "output_modalities": [str(m).lower()
                              for m in (raw.get("output_modalities") or ["text"])],
        "context_window": int(raw.get("context_window") or DEFAULT_CONTEXT_WINDOW),
        "max_output_tokens": int(raw.get("max_output_tokens") or DEFAULT_MAX_OUTPUT_TOKENS),
        "effort_levels": levels,
        "default_effort": default_effort,
    }


def _merge_defaults(new_models, saved_models):
    """Zadrži korisnikov 'default' izbor i eventualne ručne izmene imena."""
    saved = {m.get("id"): m for m in saved_models if isinstance(m, dict)}
    for m in new_models:
        old = saved.get(m["id"])
        if old:
            if old.get("default"):
                m["default"] = True
            if old.get("name"):
                m["name"] = old["name"]
    # Ako nijedan nije default -> prvi
    if new_models and not any(m.get("default") for m in new_models):
        new_models[0]["default"] = True
    return new_models


def refresh_models(api_key, timeout=30):
    """Osvježi models.json sa API-ja. Vraća (models, error_message)."""
    saved = load_models_config()
    try:
        raw = fetch_models_raw(api_key, timeout=timeout)
    except ModelCatalogError as e:
        return saved, str(e)

    models = [normalize_model(r) for r in raw]
    models = [m for m in models if m]
    if not models:
        return saved, "API nije vratio nijedan model."

    models = _merge_defaults(models, saved)
    try:
        save_models_config(models)
    except Exception as e:
        return models, f"Modeli učitani ali nisu sačuvani: {e}"
    return models, None


# ---------------------------------------------------------------------------
# POMOĆNE FUNKCIJE (čitaju cache, ne idu na mrežu)
# ---------------------------------------------------------------------------
def get_models():
    """Vraća listu modela iz cache-a (ili praznu listu)."""
    try:
        return [m for m in load_models_config() if isinstance(m, dict)]
    except Exception:
        return []


def get_model(model_id):
    """Vraća model po id-ju ili None."""
    for m in get_models():
        if m.get("id") == model_id:
            return m
    return None


def _flag_vision(m):
    """Da li model prima slike (novi format + stari 'vision': true)."""
    if not isinstance(m, dict):
        return False
    if m.get("vision"):
        return True
    mods = m.get("input_modalities") or []
    if isinstance(mods, str):
        mods = [mods]
    return any(str(x).lower() == "image" for x in mods)


def supports_images(model_id):
    """Da li dati model nativno prima slike."""
    m = get_model(model_id)
    return _flag_vision(m) if m else False


def vision_model_id():
    """Prvi model koji podržava slike (ili None)."""
    for m in get_models():
        if _flag_vision(m):
            return m.get("id")
    return None


def vision_models():
    """Svi modeli koji podržavaju slike."""
    return [m for m in get_models() if _flag_vision(m)]


def context_window(model_id):
    m = get_model(model_id) or {}
    return int(m.get("context_window") or DEFAULT_CONTEXT_WINDOW)


def max_output_tokens(model_id):
    m = get_model(model_id) or {}
    return int(m.get("max_output_tokens") or DEFAULT_MAX_OUTPUT_TOKENS)


def effort_levels(model_id):
    """Podržani reasoning_effort nivoi za model (lista, može biti prazna)."""
    m = get_model(model_id) or {}
    levels = m.get("effort_levels") or []
    return [x for x in levels if x in EFFORT_LEVELS]


def default_effort(model_id):
    m = get_model(model_id) or {}
    lvl = m.get("default_effort")
    if lvl in EFFORT_LEVELS:
        return lvl
    levels = effort_levels(model_id)
    return levels[0] if levels else None


def resolve_effort(model_id, setting):
    """'auto' -> default iz kataloga; nepoznat nivo -> default; nema -> None.

    Vraća vrednost spremnu za payload ili None (ne šaljemo polje).
    """
    levels = effort_levels(model_id)
    if not levels:
        return None
    if not setting or setting == "auto":
        return default_effort(model_id)
    return setting if setting in levels else default_effort(model_id)
