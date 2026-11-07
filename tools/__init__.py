"""Repository tooling uses only the Python standard library."""

from pathlib import Path
import sys

# Scripts import siblings by bare name; keep that working when tests import them as tools.<name>.
sys.path.insert(0, str(Path(__file__).resolve().parent))
