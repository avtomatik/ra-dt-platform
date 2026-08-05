from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "html"
EXPORTS_DIR = DATA_DIR / "exports"
SEED_DIR = DATA_DIR / "seed"

DATABASE_PATH = DATA_DIR / "radp.sqlite"
OID_REGISTRY_FIXTURE_PATH = SEED_DIR / "oid_registry.json"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
