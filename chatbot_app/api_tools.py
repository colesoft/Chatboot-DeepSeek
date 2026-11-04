# -*- coding: utf-8 -*-
"""
api_tools.py - DeepSeek Search & Fetch API (novi endpointi)
=============================================================
DeepSeek API je dobio dva nova "tools" endpointa:

  POST /v1/tools/search  -> web pretraga (DeepSeek in-house search engine)
      body: {query, count (1-50), ori_question, localization, need_content}
      resp: {"results": [{title, url, site_name, site_icon, summary,
                          content, date, authority, rerank_score}, ...]}

  POST /v1/tools/fetch   -> dohvatanje stranice kao Markdown
      body: {url}
      resp: {"title": "...", "content": "# Markdown ..."}

Ovaj modul je BEZ PyQt zavisnosti (čist stdlib) da bi mogao da se testira
iz konzole, a i da se poziva iz worker thread-ova u aplikaciji.

Sadrži:
  - search_web()      : sinhrona pretraga
  - fetch_url()       : sinhrono dohvatanje stranice
  - format_search_results() / format_fetch_result() : tekst za model/UI
  - TOOL_SCHEMAS      : OpenAI-style definicije alata za function calling
  - run_tool()        : dispatcher (ime alata -> string rezultat)
  - DeepSeekToolsError: greška sa status kodom i porukom
"""

import json
import ssl
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Endpointi (drže se i u config.py, ali ovde je fallback da modul radi sam)
# ---------------------------------------------------------------------------
try:
    from .config import DEEPSEEK_SEARCH_URL, DEEPSEEK_FETCH_URL
except Exception:  # pragma: no cover - kada se modul učitava van paketa
    DEEPSEEK_SEARCH_URL = "https://api.deepseek.com/v1/tools/search"
    DEEPSEEK_FETCH_URL = "https://api.deepseek.com/v1/tools/fetch"


# ---------------------------------------------------------------------------
# Greške
# ---------------------------------------------------------------------------
class DeepSeekToolsError(Exception):
    """Greška pri pozivu Search/Fetch API-ja."""

    def __init__(self, message, status=None, code=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code

    def __str__(self):
        if self.status:
            return f"[HTTP {self.status}] {self.message}"
        return self.message


# Preporuke za korisnika po HTTP statusu (iz zvaničnog guide-a)
_STATUS_HINTS = {
    400: "Neispravan zahtev (proveri parametre: query 1-128 znakova, count 1-50, url).",
    401: "Neispravan API ključ.",
    402: "Nema dovoljno kredita na nalogu.",
    403: "Pristup zabranjen (ključ nema dozvolu za ovaj endpoint).",
    404: "Resurs nije pronađen (proveri URL).",
    429: "Previše zahteva - sačekaj pa probaj ponovo.",
    500: "Greška na DeepSeek serveru - probaj ponovo kasnije.",
}


def _ssl_context():
    """SSL kontekst sa fallback-om.

    Na nekim Windows/Python kombinacijama učitavanje sistemskih sertifikata
    padne ("nested asn1 error"), pa tada prelazimo na neverifikovan kontekst
    (isto ponašanje kao Qt mreža u aplikaciji).
    """
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def _post_json(url, api_key, payload, timeout=45):
    """POST JSON -> dict. Podiže DeepSeekToolsError sa jasnom porukom."""
    if not api_key:
        raise DeepSeekToolsError("API ključ nije postavljen.", status=401)

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=_ssl_context()) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            pass
        msg = _STATUS_HINTS.get(e.code, f"HTTP greška {e.code}.")
        # Pokušaj da izvučeš poruku iz DeepSeek error formata
        try:
            err = json.loads(body).get("error", {})
            if err.get("message"):
                msg = err["message"]
        except Exception:
            if body.strip():
                msg = body.strip()[:300]
        raise DeepSeekToolsError(msg, status=e.code)
    except urllib.error.URLError as e:
        raise DeepSeekToolsError(f"Mrežna greška: {e.reason}")
    except Exception as e:
        raise DeepSeekToolsError(f"Neočekivana greška: {e}")

    try:
        return json.loads(raw)
    except Exception:
        raise DeepSeekToolsError("API nije vratio ispravan JSON.")


# ---------------------------------------------------------------------------
# SEARCH
# ---------------------------------------------------------------------------
def search_web(query, api_key, count=10, ori_question=None,
               localization="", need_content=False, timeout=45):
    """Web pretraga preko DeepSeek search engine-a.

    Args:
        query: upit (1-128 znakova), podržava site:, -site:, "frazu"
        api_key: DeepSeek API ključ
        count: broj rezultata (1-50, default 10)
        ori_question: originalno korisnikovo pitanje (poboljšava upit)
        localization: IP adresa za lokalizaciju rezultata ("" = default)
        need_content: ako je True, popunjava "content" (pun tekst stranice)

    Returns:
        list[dict] - rezultati (title, url, summary, content, date, ...)

    Raises:
        DeepSeekToolsError
    """
    query = (query or "").strip()
    if not query:
        raise DeepSeekToolsError("Upit za pretragu je prazan.", status=400)
    if len(query) > 128:
        query = query[:128]

    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 10
    count = max(1, min(50, count))

    payload = {"query": query, "count": count}
    if ori_question:
        payload["ori_question"] = str(ori_question).strip()[:128]
    if localization:
        payload["localization"] = str(localization).strip()
    if need_content:
        payload["need_content"] = True

    data = _post_json(DEEPSEEK_SEARCH_URL, api_key, payload, timeout=timeout)
    results = data.get("results") or []
    return results


def fetch_url(url, api_key, timeout=60):
    """Dohvata stranicu i vraća {"title": ..., "content": markdown}."""
    url = (url or "").strip()
    if not url:
        raise DeepSeekToolsError("URL je prazan.", status=400)
    if not (url.startswith("http://") or url.startswith("https://")):
        raise DeepSeekToolsError("URL mora počinjati sa http:// ili https://",
                                 status=400)
    data = _post_json(DEEPSEEK_FETCH_URL, api_key, {"url": url}, timeout=timeout)
    return {
        "title": data.get("title") or "",
        "content": data.get("content") or "",
    }


# ---------------------------------------------------------------------------
# FORMATIRANJE (za model i za UI)
# ---------------------------------------------------------------------------
def format_search_results(results, query="", max_summary=600, max_items=None):
    """Pretvara rezultate pretrage u čitljiv tekst (Markdown)."""
    if not results:
        return f'Nema rezultata za pretragu: "{query}"'

    lines = []
    if query:
        lines.append(f'🔍 Rezultati pretrage za: "{query}"')
        lines.append("")

    items = results if max_items is None else results[:max_items]
    for i, r in enumerate(items, 1):
        title = (r.get("title") or "(bez naslova)").strip()
        url = (r.get("url") or "").strip()
        site = (r.get("site_name") or "").strip()
        date = (r.get("date") or "").strip()[:10]
        summary = (r.get("summary") or r.get("content") or "").strip()

        if max_summary and len(summary) > max_summary:
            summary = summary[:max_summary].rstrip() + "..."

        head = f"{i}. {title}"
        meta = " • ".join(x for x in (site, date) if x)
        if meta:
            head += f"  ({meta})"
        lines.append(head)
        if url:
            lines.append(f"   {url}")
        if summary:
            lines.append(f"   {summary}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_fetch_result(title, content, url="", max_chars=12000):
    """Formatira rezultat fetch-a za slanje modelu."""
    out = []
    if title:
        out.append(f"📄 {title}")
    if url:
        out.append(url)
    out.append("")
    body = content or ""
    if max_chars and len(body) > max_chars:
        body = body[:max_chars].rstrip() + "\n\n[... skraćeno ...]"
    out.append(body)
    return "\n".join(out).strip()


# ---------------------------------------------------------------------------
# TOOL SCHEMAS (function calling)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Pretraži web preko DeepSeek search engine-a i vrati rangiranu "
                "listu rezultata (naslov, URL, sažetak, datum). Koristi kada "
                "su potrebne sveže informacije, dokumentacija ili činjenice "
                "koje nisu u projektu. Podržava operatore: site:, -site:, "
                '"tačna fraza".'
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Upit za pretragu (1-128 znakova).",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Broj rezultata (1-50, default 10).",
                    },
                    "need_content": {
                        "type": "boolean",
                        "description": (
                            "Ako je true, vraća i pun tekst stranice "
                            "(skuplje - koristi samo kada treba detalj)."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Dohvati sadržaj web stranice kao čist Markdown. Koristi posle "
                "web_search da pročitaš najrelevantniji rezultat u celini."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "HTTP/HTTPS URL stranice.",
                    },
                },
                "required": ["url"],
            },
        },
    },
]

TOOL_NAMES = {t["function"]["name"] for t in TOOL_SCHEMAS}


# ---------------------------------------------------------------------------
# DISPATCHER
# ---------------------------------------------------------------------------
def run_tool(name, args, api_key, ori_question=None, max_chars=12000):
    """Izvršava alat po imenu i vraća (ok: bool, tekst: str).

    Namenjeno za direktnu upotrebu u tool-call petlji chat-a:
        ok, out = run_tool("web_search", {"query": "..."}, api_key)
    """
    args = args or {}
    try:
        if name == "web_search":
            results = search_web(
                args.get("query", ""),
                api_key,
                count=args.get("count", 10),
                ori_question=args.get("ori_question") or ori_question,
                need_content=bool(args.get("need_content", False)),
            )
            return True, format_search_results(results, args.get("query", ""))

        if name == "web_fetch":
            res = fetch_url(args.get("url", ""), api_key)
            return True, format_fetch_result(res["title"], res["content"],
                                             args.get("url", ""),
                                             max_chars=max_chars)

        return False, f"Nepoznat alat: {name}"

    except DeepSeekToolsError as e:
        return False, f"❌ Greška ({name}): {e}"
    except Exception as e:
        return False, f"❌ Neočekivana greška ({name}): {e}"


if __name__ == "__main__":  # brzi smoke test iz konzole
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from chatbot_app.utils import load_api_key
    except Exception:
        def load_api_key():
            return os.environ.get("DEEPSEEK_API_KEY", "")

    key = load_api_key()
    print("API ključ:", (key[:6] + "...") if key else "NEMA")
    ok, out = run_tool("web_search", {"query": "DeepSeek API tools search",
                                      "count": 3}, key)
    print(out[:1200])
