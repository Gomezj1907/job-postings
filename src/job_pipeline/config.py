from pathlib import Path

import yaml

CONFIG_PATH = Path("config")

def load_configs() -> dict:

    with open(CONFIG_PATH / "settings.yaml", encoding = "utf-8") as f:
        return yaml.safe_load(f)
