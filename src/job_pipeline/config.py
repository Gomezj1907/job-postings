from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = ROOT / "config"
CREDENTIALS_DIR = ROOT / "credentials"
PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
def load_configs() -> dict:

    with open(CONFIG_DIR / "settings.yaml", encoding = "utf-8") as f:
        return yaml.safe_load(f)

def load_exclusions() -> dict:
    """Load exclusion criteria from the exclusions.yaml file."""
    with open(CONFIG_DIR / "exclusions.yaml", encoding = "utf-8") as f:
        return yaml.safe_load(f)