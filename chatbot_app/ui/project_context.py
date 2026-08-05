# -*- coding: utf-8 -*-
"""project_context.py - ProjectContextMixin (kontekst projekta + izbor foldera)."""
import os
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog
from ..utils import save_project_path
from ..logger import log


class ProjectContextMixin:
    """Kontekst projekta i izbor foldera."""

    # ⏱️ Debounce: čuvaj na disk max jednom u 2 sekunde (sprečava sporost
    # kad AI pozove 20 alata u petlji - svaki bi pisao fajl!)
    _ctx_save_timer = None
    _ctx_save_pending = False

    def _get_project_context_path(self):
        """Vraća putanju do fajla sa kontekstom projekta.
        ✅ Namerno u PROJECT folderu - svaki projekat ima svoj kontekst,
        da se 2-3 projekta ne mešaju!"""
        return os.path.join(self.project_path, ".deepseek_context.txt")
    
    def _load_project_context(self):
        """Učitava kontekst projekta iz .deepseek_context.txt."""
        ctx_path = self._get_project_context_path()
        if os.path.exists(ctx_path):
            try:
                with open(ctx_path, "r", encoding="utf-8") as f:
                    self.project_context = f.read().strip()
                print(f"[DeepSeek] Učitan kontekst projekta ({len(self.project_context)} chars)")
            except:
                self.project_context = ""
        else:
            self.project_context = ""
    
    def _save_project_context(self, text):
        """Dodaje tekst u kontekst projekta.
        ⚠️ Debounce: menja memoriju odmah, ali piše na disk max 1x/2s."""
        if not text:
            return
        if self.project_context:
            self.project_context += "\n" + text
        else:
            self.project_context = text
        
        # ⚠️ Ograniči kontekst na ~30KB (inače će narasti ogromno
        # i usporiti/preskupiti svaki API poziv jer ide u system prompt).
        # Zadržavamo POSLEDNJIH 30KB (najnoviji rad).
        MAX_CONTEXT_CHARS = 30000
        if len(self.project_context) > MAX_CONTEXT_CHARS:
            self.project_context = self.project_context[-MAX_CONTEXT_CHARS:]
            # Obeleži da je kontekst skraćen
            marker = f"\n[Kontekst je skraćen na poslednjih {MAX_CONTEXT_CHARS} karaktera - stariji rad je u history fajlu]"
            self.project_context = marker + self.project_context
        
        # 🧹 AUTO-KOMPAKTIZACIJA u memoriji (bez čekanja diska)
        self._compact_project_context()
        
        # ⏱️ Debounce pisanje na disk - ako već čekamo, samo obeleži
        if self._ctx_save_pending:
            return
        self._ctx_save_pending = True
        
        # Iskoristi QTimer za odloženo pisanje (import na vrhu)
        try:
            from PyQt5.QtCore import QTimer
            if self._ctx_save_timer is None:
                self._ctx_save_timer = QTimer()
                self._ctx_save_timer.setSingleShot(True)
                self._ctx_save_timer.timeout.connect(self._flush_project_context)
            self._ctx_save_timer.start(2000)  # 2 sekunde
        except Exception:
            # Fallback: piši odmah ako QTimer nije dostupan
            self._flush_project_context()
    
    def _flush_project_context(self):
        """Stvarno piše kontekst na disk (poziva ga QTimer debounce)."""
        self._ctx_save_pending = False
        ctx_path = self._get_project_context_path()
        try:
            with open(ctx_path, "w", encoding="utf-8") as f:
                f.write(self.project_context)
            print(f"[DeepSeek] Sačuvan kontekst projekta ({len(self.project_context)} chars)")
        except Exception as e:
            print(f"[DeepSeek] Greška pri čuvanju konteksta: {e}")

    def _compact_project_context(self, max_entries=300, keep_recent=40):
        """Sažima najstarije unose konteksta da fajl ne raste beskonačno.

        Kada broj unosa pređe max_entries:
        - Najstariji unosi se sažmu u JEDAN unos "📋 SAŽETAK STAROG KONTEKSTA"
        - Zadržavaju se poslednjih keep_recent sirovih unosa (najnoviji rad)

        ⚠️ VAŽNO: rezultat kompaktizacije MORA biti ispod max_entries!
        (keep_recent + max 100 sažetih ≈ 140 < 300) - inače se vrti u petlji.
        """
        try:
            lines = [l.strip() for l in self.project_context.split("\n") if l.strip()]
            if len(lines) <= max_entries:
                return  # nema potrebe za kompaktizacijom

            old_count = len(lines) - keep_recent
            old_lines = lines[:old_count]      # najstariji (za sažetak)
            recent_lines = lines[-keep_recent:]  # najnoviji (zadržavamo)

            # Sažmi stare unose - uzmi samo prve reči/suštinu svakog
            compact_parts = []
            for l in old_lines:
                # Skrati na 80 karaktera - dovoljno za "šta je rađeno"
                short = l[:80]
                compact_parts.append("- " + short)

            # Ograniči i sam sažetak (max ~100 unosa u sažetku)
            if len(compact_parts) > 100:
                compact_parts = compact_parts[:100] + ["- ... (stariji unosi obrisani)"]

            first_date = old_lines[0][:16] if old_lines else "?"
            last_date = old_lines[-1][:16] if old_lines else "?"
            summary_block = (
                f"## 📋 SAŽETAK STAROG KONTEKSTA ({first_date} → {last_date})\n"
                + "\n".join(compact_parts)
            )

            self.project_context = summary_block + "\n\n## 🆕 NAJNOVIJI RAD\n" + "\n".join(recent_lines)
            log(f"🧹 Kompaktizovan kontekst: {len(lines)} unosa → {len(compact_parts)} sažetih + {len(recent_lines)} najnovijih")
            print(f"[DeepSeek] Kontekst kompaktizovan: {len(lines)} → {len(compact_parts) + len(recent_lines)} unosa")
        except Exception as e:
            print(f"[DeepSeek] Greška pri kompaktizaciji konteksta: {e}")
    def _append_project_context(self, user_msg, assistant_msg):
        """Dodaje poruku u kontekst projekta (samo bitne stvari)."""
        # Sažmi poruku - samo suština
        # 📈 Povećano sa 100/200 na 400/1500 karaktera da kontekst ima više sadržaja
        context_entry = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {user_msg[:400]} → {assistant_msg[:1500]}"
        self._save_project_context(context_entry)

    def _get_project_context_summary(self, max_entries=10, max_chars_per_entry=250, max_total=4000):
        """Vraća SAŽETAK konteksta projekta (ne ceo fajl!).
        
        Umesto da šaljemo ceo .deepseek_context.txt (30KB+) na svaki API poziv,
        šaljemo samo BITNE unose - "do sad promenjeno to i to".

        Prioritet:
        1. 🔧/✏️/📄 create_file/edit_file unosi (bitne promene) - uvek
        2. 💻 run_command unosi - skraćeni na 80 chars (nisu toliko bitni)
        3. Ostali unosi (AI zaključci sa →)

        Args:
            max_entries: koliko ukupno unosa prikazati
            max_chars_per_entry: max dužina svakog unosa
            max_total: max ukupna dužina sažetka (karaktera)
        """
        if not self.project_context:
            return ""
        
        # Kontekst fajl je niz linija: [datum vreme] opis
        lines = [l.strip() for l in self.project_context.split("\n") if l.strip()]
        total_entries = len(lines)
        
        # Podeli unose po tipu
        important = []   # create/edit - bitne promene
        conclusions = []  # AI zaključci (sadrže →)
        commands = []     # run_command
        
        for line in lines:
            if "🔧 create_file" in line or "✏️ edit_file" in line:
                important.append(line)
            elif "💻 run_command" in line:
                commands.append(line)
            elif "→" in line:
                conclusions.append(line)
            else:
                conclusions.append(line)
        
        # Uzmi najnovije iz svake grupe
        n_important = min(5, len(important))
        n_conclusions = min(3, len(conclusions))
        n_commands = min(2, len(commands))
        
        picked = []
        picked += important[-n_important:]
        picked += conclusions[-n_conclusions:]
        picked += commands[-n_commands:]
        
        # Skrati svaki unos
        shortened = []
        for line in picked:
            max_len = 80 if "run_command" in line else max_chars_per_entry
            if len(line) > max_len:
                line = line[:max_len] + "..."
            shortened.append("• " + line)
        
        body = "\n".join(shortened)
        # Ako i dalje prelazi limit, uzmi poslednji deo (najnovije)
        if len(body) > max_total:
            body = "…" + body[-(max_total - 1):]
        
        header = f"## Kontekst projekta (sažetak)"
        if total_entries > len(picked):
            header += f" - ukupno {total_entries} unosa u istoriji, prikazano {len(picked)} najbitnijih"
        
        summary = f"{header}\n{body}"
        log(f"📋 Sažetak konteksta: {len(summary)} chars (~{len(summary)//4} tokena) od ukupno {len(self.project_context)} chars")
        return summary

    def _choose_project_path(self):
        """Bira projektni direktorijum."""
        path = QFileDialog.getExistingDirectory(
            self, "Izaberi projektni direktorijum",
            self.project_path
        )
        if path:
            self.project_path = path
            save_project_path(path)
            self.lbl_project.setText(self._short_path(path, 40))
            self.status_label.setText(f"📁 Projekat: {path}")
            self._load_project_context()  # Učitaj kontekst za novi projekat
            self._clear_chat()


# =============================================================================
