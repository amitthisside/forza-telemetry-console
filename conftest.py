import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for candidate in ROOT.glob('services/*/src'):
    sys.path.insert(0, str(candidate))

for candidate in ROOT.glob('packages/*/src'):
    sys.path.insert(0, str(candidate))
