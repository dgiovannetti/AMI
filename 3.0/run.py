#!/usr/bin/env python3
"""
Avvio rapido AMI 3.0 da sorgente.
Esegui dalla cartella 3.0:  python run.py
"""
import sys
from pathlib import Path

# Aggiungi src al path così che "ami" sia importabile
root = Path(__file__).resolve().parent
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from ami.main import main

if __name__ == "__main__":
    main()
