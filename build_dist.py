"""
build_dist.py - Kreira distribucioni paket za DeepSeek Chatbot
Koristi 7-Zip SFX za self-extracting archive sa ikonom.
"""
import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess
import struct

# ============================================================
# KONFIGURACIJA
# ============================================================
APP_NAME = "DeepSeek Chatbot"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(APP_DIR, "dist")
BUILD_DIR = os.path.join(APP_DIR, "build_temp")
SEVEN_ZIP_URL = "https://github.com/cole/7z-extra/releases/download/v1.0/7z-extra.zip"
SEVEN_ZIP_URL_ALT = "https://www.7-zip.org/a/7z2409-extra.7z"

# Fajlovi koji idu u distribuciju
DIST_FILES = [
    "main.py",
    "deepseek_chatbot.py",
    "run.bat",
    "deepseek.ico",
    "requirements.txt",
    "README.md",
    "LICENSE",
    "rs.jpg",
    "cn.jpg"
]

# Paket chatbot_app/ (rekurzivno)
DIST_DIRS = [
    "chatbot_app",
]

# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================

def print_step(step, msg):
    print(f"\n  {'='*50}")
    print(f"  [{step}] {msg}")
    print(f"  {'='*50}")

def download_file(url, dest):
    """Skida fajl sa URL-a."""
    print(f"  ⬇️  Preuzimam: {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"  ❌ Greška: {e}")
        return False

def ensure_dir(path):
    """Kreira direktorijum ako ne postoji."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"  📁 Kreiran: {path}")

def find_7z():
    """Traži 7z.exe na sistemu."""
    # Prvo proveri Program Files
    for path in [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]:
        if os.path.exists(path):
            return path
    
    # Probaj u build temp
    build_7z = os.path.join(BUILD_DIR, "7z.exe")
    if os.path.exists(build_7z):
        return build_7z
    
    # Probaj u dist folderu
    dist_7z = os.path.join(DIST_DIR, "7z.exe")
    if os.path.exists(dist_7z):
        return dist_7z
    
    return None

# ============================================================
# GLAVNA FUNKCIJA
# ============================================================

def build_dist():
    print(f"""
  {'='*60}
  🚀 DeepSeek Chatbot - Build Distribution
  {'='*60}
    """)
    
    # 1. Proveri da li ikonica postoji
    print_step("1/6", "Provera ikonice")
    ico_path = os.path.join(APP_DIR, "deepseek.ico")
    if not os.path.exists(ico_path):
        print("  ❌ Ikonica ne postoji! Pokreni create_icon.py prvo.")
        return False
    print(f"  ✅ Ikonica: {ico_path} ({os.path.getsize(ico_path)} bytes)")
    
    # 2. Proveri fajlove
    print_step("2/6", "Provera fajlova za distribuciju")
    missing = []
    for f in DIST_FILES:
        fpath = os.path.join(APP_DIR, f)
        if not os.path.exists(fpath):
            missing.append(f)
        else:
            print(f"  ✅ {f}")
    
    if missing:
        print(f"  ❌ Nedostaju fajlovi: {', '.join(missing)}")
        return False
    
    # 3. Pronađi ili skini 7-Zip
    print_step("3/6", "Pronalazak 7-Zip")
    seven_zip = find_7z()
    
    if seven_zip:
        print(f"  ✅ 7z pronađen: {seven_zip}")
    else:
        print("  ⬇️  7z nije pronađen. Skidam portable verziju...")
        ensure_dir(BUILD_DIR)
        
        # Skini 7z extra (sadrži 7z.exe, 7z.sfx, 7zSD.sfx)
        zip_path = os.path.join(BUILD_DIR, "7z-extra.zip")
        if not download_file(SEVEN_ZIP_URL, zip_path):
            # Alternativni URL
            print("  ⚠️  Probam alternativni URL...")
            if not download_file(SEVEN_ZIP_URL_ALT, zip_path):
                print("  ❌ Ne mogu da skinem 7-Zip!")
                print("  Preuzmi 7-Zip sa: https://www.7-zip.org/download.html")
                print("  i instaliraj ga, pa pokreni ponovo.")
                return False
        
        # Raspakuj
        print("  📦 Raspakujem...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(BUILD_DIR)
        except:
            # Možda je .7z format
            import subprocess
            # Ako imamo 7z u PATH-u
            try:
                subprocess.run(["7z", "x", zip_path, f"-o{BUILD_DIR}", "-y"], check=True)
            except:
                print("  ❌ Ne mogu da raspakujem 7z fajl.")
                return False
        
        seven_zip = find_7z()
        if not seven_zip:
            print("  ❌ 7z.exe nije pronađen nakon raspakivanja!")
            return False
        print(f"  ✅ 7z spreman: {seven_zip}")
    
    # 4. Pronađi SFX module
    print_step("4/6", "Pronalazak SFX modula")
    
    sfx_sd = os.path.join(os.path.dirname(seven_zip), "7zSD.sfx")
    sfx_sd_alt = os.path.join(BUILD_DIR, "7zSD.sfx")
    sfx_sd_alt2 = os.path.join(DIST_DIR, "7zSD.sfx")
    
    # Probaj na više mesta
    sfx_path = None
    for p in [sfx_sd, sfx_sd_alt, sfx_sd_alt2]:
        if os.path.exists(p):
            sfx_path = p
            break
    
    if not sfx_path:
        # Probaj da nađeš bilo koji .sfx fajl
        for root, dirs, files in os.walk(BUILD_DIR):
            for f in files:
                if f.endswith(".sfx"):
                    sfx_path = os.path.join(root, f)
                    break
            if sfx_path:
                break
    
    if not sfx_path:
        # Ako nemamo 7zSD.sfx (koji podržava ikone), koristimo običan 7z.sfx
        sfx_normal = os.path.join(os.path.dirname(seven_zip), "7z.sfx")
        if os.path.exists(sfx_normal):
            sfx_path = sfx_normal
            print("  ⚠️  Koristim običan 7z.sfx (bez custom ikone)")
        else:
            print("  ❌ SFX modul nije pronađen!")
            return False
    
    print(f"  ✅ SFX modul: {sfx_path}")
    
    # 5. Napravi 7z arhivu
    print_step("5/6", "Pravljenje 7z arhive")
    ensure_dir(DIST_DIR)
    
    archive_path = os.path.join(DIST_DIR, "deepseek.7z")
    
    # Kopiraj fajlove u build temp
    ensure_dir(BUILD_DIR)
    app_build = os.path.join(BUILD_DIR, APP_NAME)
    ensure_dir(app_build)
    
    for f in DIST_FILES:
        src = os.path.join(APP_DIR, f)
        dst = os.path.join(app_build, f)
        shutil.copy2(src, dst)
        print(f"  📄 {f}")
    
    # Kopiraj chatbot_app/ paket (svi .py fajlovi rekurzivno)
    for d in DIST_DIRS:
        src_dir = os.path.join(APP_DIR, d)
        dst_dir = os.path.join(app_build, d)
        if os.path.isdir(src_dir):
            shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns("__pycache__", "*.bak"))
            for root, dirs, files in os.walk(dst_dir):
                for fn in files:
                    print(f"  📄 {os.path.relpath(os.path.join(root, fn), app_build)}")
    
    # Dodaj i create_icon.py
    shutil.copy2(os.path.join(APP_DIR, "create_icon.py"), os.path.join(app_build, "create_icon.py"))
    print(f"  📄 create_icon.py")
    
    # Napravi 7z arhivu
    cmd = [
        seven_zip, "a", "-t7z", "-mx=9", "-mfb=273", "-ms=on",
        archive_path,
        f"{app_build}\\*"
    ]
    
    print(f"  ⏳ Arhiviram...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ Greška pri arhiviranju:")
        print(result.stderr)
        return False
    
    archive_size = os.path.getsize(archive_path)
    print(f"  ✅ Arhiva: {archive_path} ({archive_size / 1024:.1f} KB)")
    
    # 6. Napravi SFX izvršni fajl
    print_step("6/6", "Pravljenje SFX izvršnog fajla")
    
    # Konfiguracija za SFX
    sfx_config = f"""; SFX konfiguracija za DeepSeek Chatbot
;-------------------------------------------------
Title={APP_NAME}
BeginPrompt=Instalacija DeepSeek Chatbot asistenta
FinishPrompt=Aplikacija je spremna! Pokreni je sada?
ExtractPath=%USERPROFILE%\\Desktop\\{APP_NAME}
ExtractPathTitle=Odaberi destinaciju
ExtractPathText=Gde zelis da instaliras aplikaciju?
RunProgram=run.bat
RunProgramAfterExtract=run.bat
OverwriteMode=a
"""
    
    config_path = os.path.join(BUILD_DIR, "sfx_config.txt")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(sfx_config)
    
    sfx_output = os.path.join(DIST_DIR, f"{APP_NAME}_Setup.exe")
    
    # Spoji SFX modul + config + 7z arhivu
    with open(sfx_output, "wb") as out:
        # SFX modul
        with open(sfx_path, "rb") as sfx:
            out.write(sfx.read())
        
        # Konfiguracija
        with open(config_path, "rb") as cfg:
            out.write(cfg.read())
        
        # 7z arhiva
        with open(archive_path, "rb") as arc:
            out.write(arc.read())
    
    # Proveri da li SFX podržava custom ikone
    # Ako koristimo 7zSD.sfx (koji podržava), dodajemo ikonu
    if "7zSD" in os.path.basename(sfx_path):
        # Za 7zSD.sfx, ikona se može dodati sa Resource Hacker ili .rsrc
        # Nažalost, ne možemo lako da dodamo ikonu u .exe bez Resource Hackera
        print("  ⚠️  Za custom ikonu u SFX-u, koristi Resource Hacker:")
        print(f"     ResHacker.exe -add {sfx_output}, {sfx_output}, deepseek.ico, ICONGROUP, MAINICON, 0")
    
    # Ako koristimo običan 7z.sfx, ne može custom ikona
    # Napravi i ZIP verziju kao fallback
    zip_output = os.path.join(DIST_DIR, f"{APP_NAME}_Portable.zip")
    with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in DIST_FILES:
            zf.write(os.path.join(APP_DIR, f), f)
        # chatbot_app/ paket rekurzivno
        for root, dirs, files in os.walk(os.path.join(APP_DIR, "chatbot_app")):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                if fn.endswith(".bak"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, APP_DIR)
                zf.write(full, rel)
        zf.write(ico_path, "deepseek.ico")
    
    exe_size = os.path.getsize(sfx_output)
    zip_size = os.path.getsize(zip_output)
    
    print(f"""
  {'='*60}
  ✅ DISTRIBUCIJA KREIRANA!
  {'='*60}
  
  📦 SFX Installer: {sfx_output}
     Veličina: {exe_size / 1024 / 1024:.1f} MB
  
  📦 ZIP Portable: {zip_output}
     Veličina: {zip_size / 1024 / 1024:.1f} MB
  
  📁 Izvorni fajlovi: {APP_DIR}
  
  🚀 Pokreni SFX da instaliras aplikaciju!
  {'='*60}
    """)
    
    # Očisti temp
    print("  🧹 Čistim temp fajlove...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    
    return True

if __name__ == "__main__":
    build_dist()
