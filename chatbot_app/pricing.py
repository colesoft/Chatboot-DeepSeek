# -*- coding: utf-8 -*-
"""
pricing.py - DeepSeek cene i optimizacija troškova
====================================================
Strategija (iz https://api-docs.deepseek.com/quick_start/pricing):

- ŠPIC (PEAK) sati (UTC): 01:00–04:00  i  06:00–10:00
  → cene su DUPLO veće (regularna tarifa)
- VAN ŠPICA (OFF-PEAK, sve ostalo): → 50% POPUST
- CACHE HIT (context caching): ulazni tokeni iz keša koštaju
  samo 10% cene ulaznih tokena (90% uštede!)
- Preporuka: teške zadatke (veliki context, duži output) raditi
  van špica; kratke dnevne upite raditi na deepseek-v4-flash.

Cene po 1M tokena (USD). Pro = ~2x flash. Ažurirati po potrebi
(preko "Proveri cene" dugmeta otvara zvaničnu stranicu).
"""

from datetime import datetime, timezone

# =============================================================================
# CENE (USD po 1.000.000 tokena)
# =============================================================================
# Ključ: model id → (input cache-miss, input cache-hit, output)
# Cache-hit = 10% cene inputa (90% uštede).
PRICES = {
    "deepseek-v4-flash": {
        "input_miss": 0.28,   # $/1M ulaznih tokena (bez keša)
        "input_hit":  0.028,  # $/1M ulaznih tokena (iz keša, -90%)
        "output":     0.42,   # $/1M izlaznih tokena
    },
    "deepseek-v4-pro": {
        "input_miss": 0.56,   # ~2x flash
        "input_hit":  0.056,
        "output":     0.84,
    },
    # Fallback (stari modeli) → ista tarifa kao flash
    "deepseek-chat": {
        "input_miss": 0.28,
        "input_hit":  0.028,
        "output":     0.42,
    },
    "deepseek-reasoner": {
        "input_miss": 0.28,
        "input_hit":  0.028,
        "output":     0.42,
    },
}

# DeepSeek ne vraća naziv modela u usage-u, ali mi znamo koji smo poslali.
DEFAULT_PRICE = PRICES["deepseek-v4-flash"]

# =============================================================================
# ŠPIC / VAN ŠPICA (UTC)
# =============================================================================
# Špic: 01:00–04:00 UTC  i  06:00–10:00 UTC (intervali su [start, end))
# Van špica: sve ostalo → 50% popust na input i output.
PEAK_WINDOWS = [
    (1, 4),    # 01:00–04:00 UTC
    (6, 10),   # 06:00–10:00 UTC
]
OFF_PEAK_DISCOUNT = 0.5  # 50% popust


def is_off_peak(now=None):
    """Vraća True ako je trenutno VAN ŠPICA (jeftinije).

    now: datetime (lokalni) ili None → koristi trenutno vreme UTC.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    # Normalizuj na UTC
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    hour = now.astimezone(timezone.utc).hour
    for start, end in PEAK_WINDOWS:
        if start <= hour < end:
            return False
    return True


def peak_window_text():
    """Tekstualni opis špica (za tooltip)."""
    return "Špic (UTC): 01–04h i 06–10h — cene duplo veće\nVan špica: −50% popust"


def get_price(model_id):
    """Vraća cenovnik za model (ili default ako model ne postoji)."""
    if model_id in PRICES:
        return PRICES[model_id]
    # Probaj da nađeš po prefiksu (npr. deepseek-v4-flash-xxx)
    for key in PRICES:
        if model_id.startswith(key):
            return PRICES[key]
    return DEFAULT_PRICE


# =============================================================================
# MAKSIMALNI BROJ IZLAZNIH TOKENA PO MODELU
# =============================================================================
def get_max_tokens(model_id):
    """max_tokens po modelu:
    - deepseek-v4-* : 32768 (novi modeli podržavaju dugačak output)
    - ostali (V3.2-Exp i sl.) : 8192 (više od toga API odbija)
    """
    if "v4" in model_id:
        return 32768
    return 8192


# =============================================================================
# PROCENA TROŠKA
# =============================================================================
def estimate_cost(model_id, usage, apply_off_peak=True):
    """Računa cenu zahteva u USD na osnovu usage odgovora API-ja.

    usage (dict) može da sadrži:
      - prompt_tokens
      - prompt_cache_hit_tokens     (ulaz iz keša → -90%)
      - prompt_cache_miss_tokens    (ulaz van keša)
      - completion_tokens
    Ako cache polja ne postoje, svi prompt tokeni se tretiraju kao miss.
    """
    if not usage or not isinstance(usage, dict):
        return 0.0

    price = get_price(model_id)

    prompt_total = usage.get("prompt_tokens", 0) or 0
    hit = usage.get("prompt_cache_hit_tokens", 0) or 0
    miss = usage.get("prompt_cache_miss_tokens", None)
    if miss is None:
        miss = max(prompt_total - hit, 0)
    completion = usage.get("completion_tokens", 0) or 0

    # Cene po tokenu
    input_miss_cost = price["input_miss"] / 1_000_000
    input_hit_cost = price["input_hit"] / 1_000_000
    output_cost = price["output"] / 1_000_000

    cost = (miss * input_miss_cost + hit * input_hit_cost + completion * output_cost)

    # Popust van špica
    if apply_off_peak and is_off_peak():
        cost *= (1.0 - OFF_PEAK_DISCOUNT)

    return cost


def format_usd(cost):
    """Formatira cenu u USD: $0.0042 ili $0.00 ako je zanemarljiva."""
    if cost >= 1:
        return f"${cost:.2f}"
    if cost >= 0.01:
        return f"${cost:.4f}"
    return f"${cost:.6f}"


# =============================================================================
# KONVERZIJA USD -> CNY
# =============================================================================
# DeepSeek balans stiže u CNY (yuan), pa i potrošnju prikazujemo u CNY da
# budu konzistentni. Ovo je približan fiksni kurs - ažurirati po potrebi.
USD_TO_CNY = 7.2


def usd_to_cny(cost_usd):
    """Konvertuje iznos iz USD u CNY po fiksnom kursu."""
    return cost_usd * USD_TO_CNY


def format_cny(cost_usd):
    """Formatira potrošnju (koja je interno u USD) kao CNY: ¥0.03 ili ¥0.00."""
    cny = usd_to_cny(cost_usd)
    if cny >= 1:
        return f"¥{cny:.2f}"
    if cny >= 0.01:
        return f"¥{cny:.4f}"
    if cny >= 0.0001:
        return f"¥{cny:.6f}"
    return "¥0.00"


def cache_savings_pct(usage):
    """Koliko procenata ulaznih tokena je serviran iz keša (0-100)."""
    if not usage or not isinstance(usage, dict):
        return 0.0
    hit = usage.get("prompt_cache_hit_tokens", 0) or 0
    total = usage.get("prompt_tokens", 0) or 0
    if total <= 0:
        return 0.0
    return (hit / total) * 100.0
