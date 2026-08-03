#!/bin/bash
# ============================================================
# DeepSeek Code Assistant - Linux pokretanje
# ============================================================
# Autor: Cole_Soft (c) 2026
# Web: https://www.colesoft.net
# ============================================================
#
# Instalacija (samo prvi put):
#   chmod +x run.sh
#   pip install PyQt5
#
# Pokretanje:
#   ./run.sh
# ============================================================

# Putanja do skripte (radi i iz drugog direktorijuma)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Provera da li Python postoji
if ! command -v python3 &> /dev/null; then
    echo "Python 3 nije instaliran!"
    echo "Instaliraj ga: sudo apt install python3 python3-pip"
    exit 1
fi

# Provera da li PyQt5 postoji
python3 -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "PyQt5 nije instaliran. Instaliram..."
    pip install PyQt5
    if [ $? -ne 0 ]; then
        echo "Greska pri instalaciji PyQt5!"
        echo "Pokusaj: sudo apt install python3-pyqt5"
        exit 1
    fi
fi

# Provera da li postoji glavni fajl
if [ ! -f "main.py" ]; then
    echo "Fajl main.py nije pronadjen!"
    exit 1
fi

# Pokreni aplikaciju
echo "Pokrecem DeepSeek Code Assistant..."
python3 main.py "$@"
