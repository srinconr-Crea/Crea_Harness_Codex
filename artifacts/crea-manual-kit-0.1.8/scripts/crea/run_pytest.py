"""Entrada local explícita al pytest preparado; no instala herramientas."""
import sys
from pathlib import Path
import pytest

if __name__=='__main__':
    sys.path.insert(0,str(Path.cwd().resolve()))
    raise SystemExit(pytest.main(['-p','testing.pytest_inventory',*sys.argv[1:]]))
