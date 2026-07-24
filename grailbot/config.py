"""Configuration. Reads a .env file (if present) then the environment.

No third-party dependency required: if python-dotenv is installed we use it,
otherwise a tiny built-in parser handles the .env file. This keeps mock mode
runnable on a bare Python install.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str | os.PathLike = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    try:  # prefer the real library if available
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(p, override=False)
        return
    except Exception:
        pass
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.split("#", 1)[0].strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def _f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    mode: str = "mock"                     # "mock" | "live"
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_marketplace: str = "EBAY_US"
    price_vendor: str = "mock"             # "mock" | "sportscardspro" | "cardhedge"
    price_vendor_api_key: str = ""
    fee_rate: float = 0.1325
    ship_out: float = 5.00
    min_net_edge: float = 15.00
    min_identity_confidence: float = 0.70
    value_floor: float = 8.00
    db_path: str = "grailbot.db"

    @classmethod
    def load(cls, dotenv: str | os.PathLike = ".env") -> "Settings":
        _load_dotenv(dotenv)
        e = os.environ
        return cls(
            mode=e.get("GRAILBOT_MODE", "mock").lower(),
            ebay_client_id=e.get("EBAY_CLIENT_ID", ""),
            ebay_client_secret=e.get("EBAY_CLIENT_SECRET", ""),
            ebay_marketplace=e.get("EBAY_MARKETPLACE", "EBAY_US"),
            price_vendor=e.get("PRICE_VENDOR", "mock").lower(),
            price_vendor_api_key=e.get("PRICE_VENDOR_API_KEY", ""),
            fee_rate=_f("EBAY_FEE_RATE", 0.1325),
            ship_out=_f("DEFAULT_SHIP_OUT", 5.00),
            min_net_edge=_f("MIN_NET_EDGE", 15.00),
            min_identity_confidence=_f("MIN_IDENTITY_CONFIDENCE", 0.70),
            value_floor=_f("VALUE_FLOOR", 8.00),
            db_path=e.get("DB_PATH", "grailbot.db"),
        )

    @property
    def is_live(self) -> bool:
        return self.mode == "live"
