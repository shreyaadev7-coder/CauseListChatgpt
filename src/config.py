from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    website_url: str
    bench: str
    search_by: str
    advocate_name: str
    days_ahead: int
    no_cases_action: str
    prefer_get_details: bool


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "settings.json"


def load_settings() -> Settings:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Settings(**data)
