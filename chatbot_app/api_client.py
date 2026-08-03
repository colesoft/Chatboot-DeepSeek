# -*- coding: utf-8 -*-
"""
api_client.py - DeepSeek API logika (čiste funkcije)
======================================================
- validate_and_fix_messages: popravlja poruke pre slanja API-ju
  (sprečava grešku 400 "assistant message with 'tool_calls' must be
  followed by tool messages")

U budućnosti (Faza 3): ceo API klijent (pozivi, streaming, modeli, balans).
"""


def validate_and_fix_messages(msgs):
    """Validira poruke pre slanja API-ju i popravlja problematične.

    DeepSeek API vraća 400 grešku:
    "An assistant message with 'tool_calls' must be followed by tool
    messages responding to each 'tool_call_id'. (insufficient tool
    messages following tool_calls message)"

    Ovo se dešava kad:
    - Korisnik pritisne ⛔ STOP usred tool petlje
    - History sažimanje odseče tool poruke
    - Učitana sesija ima nedovršene tool pozive
    - Assistant poruka sa tool_calls ostane bez odgovora

    Rešenje:
    - Ako assistant poruka ima tool_calls bez pratećih tool poruka,
      dodajemo fallback tool poruke da API prihvati zahtev.
    - Brišemo "viseće" tool poruke koje nemaju odgovarajućeg pretka.
    """
    if not msgs:
        return msgs

    # 🔧 Spoji više uzastopnih system poruka u jednu (DeepSeek API to zahteva)
    merged = []
    system_content_parts = []
    for msg in msgs:
        if msg.get("role") == "system":
            system_content_parts.append(msg.get("content", ""))
        else:
            if system_content_parts:
                merged.append({"role": "system", "content": "\n\n".join(system_content_parts)})
                system_content_parts = []
            merged.append(msg)
    if system_content_parts:
        merged.append({"role": "system", "content": "\n\n".join(system_content_parts)})
    msgs = merged

    fixed = []
    pending_tool_ids = set()  # tool_call_id-jevi koji čekaju odgovor

    for msg in msgs:
        role = msg.get("role")

        # ---- tool poruka ----
        if role == "tool":
            tc_id = msg.get("tool_call_id")
            # Ako tool poruka nema pretka sa tool_calls, obriši je
            if tc_id not in pending_tool_ids:
                continue  # viseća tool poruka - preskoči
            pending_tool_ids.discard(tc_id)
            fixed.append(msg)
            continue

        # ---- ostale poruke (user, assistant, system) ----
        # ⚠️ VAŽNO: Ako ima neodgovorenih tool_call_id-jeva, moramo dodati
        # fallback tool poruke ODMAH PRE ove poruke, jer DeepSeek API
        # zahteva da tool poruke slede assistant tool_calls poruku pre
        # bilo koje druge poruke. Dodavanje na kraj liste ne pomaže -
        # API i dalje vraća 400!
        if pending_tool_ids:
            for tc_id in pending_tool_ids:
                fixed.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": "[Tool call interrupted - no result available. Continue without it.]"
                })
            pending_tool_ids = set()

        fixed.append(msg)

        # Ako je assistant sa tool_calls, zapamti koje id-jeve očekujemo
        if role == "assistant" and msg.get("tool_calls"):
            pending_tool_ids = set()
            for tc in msg["tool_calls"]:
                tc_id = tc.get("id")
                if tc_id:
                    pending_tool_ids.add(tc_id)

    # Ako na kraju ima neodgovorenih tool_call_id-jeva,
    # dodaj fallback tool poruke da API ne vrati 400
    for tc_id in pending_tool_ids:
        fixed.append({
            "role": "tool",
            "tool_call_id": tc_id,
            "content": "[Tool call interrupted - no result available. Continue without it.]"
        })

    return fixed
