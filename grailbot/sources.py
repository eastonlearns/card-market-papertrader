"""Data sources: active listings (eBay) + sold comps (price vendor).

Every source implements a tiny interface, so mock and live are interchangeable
and the pipeline never knows which it's talking to. Live clients lazily import
httpx so mock mode stays stdlib-only.
"""
from __future__ import annotations

from typing import Optional, Protocol

from grailbot.config import Settings
from grailbot.models import Card, Comp, Listing


class ListingSource(Protocol):
    def search(self, query: str, limit: int = 50) -> list[Listing]: ...


class CompSource(Protocol):
    def get_comp(self, card: Card) -> Optional[Comp]: ...


# --------------------------------------------------------------------------
# Mock implementations (bundled sample data — no network, no keys)
# --------------------------------------------------------------------------
class MockListingSource:
    def __init__(self, listings: list[Listing]):
        self._listings = listings

    def search(self, query: str, limit: int = 50) -> list[Listing]:
        q = query.lower().strip()
        hits = [l for l in self._listings if not q or q in l.title.lower()]
        return hits[:limit]


class MockCompSource:
    def __init__(self, comps: dict[str, Comp]):
        self._comps = comps

    def get_comp(self, card: Card) -> Optional[Comp]:
        return self._comps.get(card.key())


# --------------------------------------------------------------------------
# Live implementations (skeletons — wired, waiting only on your keys)
# --------------------------------------------------------------------------
class EbayBrowseSource:
    """eBay Browse API (active listings). Client-credentials OAuth."""
    TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    def __init__(self, settings: Settings):
        self.s = settings
        self._token: Optional[str] = None

    def _client(self):
        import httpx  # lazy
        return httpx.Client(timeout=20)

    def _auth(self) -> str:
        if self._token:
            return self._token
        import base64
        creds = base64.b64encode(
            f"{self.s.ebay_client_id}:{self.s.ebay_client_secret}".encode()
        ).decode()
        with self._client() as c:
            r = c.post(
                self.TOKEN_URL,
                headers={"Authorization": f"Basic {creds}",
                         "Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials",
                      "scope": "https://api.ebay.com/oauth/api_scope"},
            )
            r.raise_for_status()
            self._token = r.json()["access_token"]
        return self._token

    def search(self, query: str, limit: int = 50) -> list[Listing]:
        with self._client() as c:
            r = c.get(
                self.SEARCH_URL,
                headers={"Authorization": f"Bearer {self._auth()}",
                         "X-EBAY-C-MARKETPLACE-ID": self.s.ebay_marketplace},
                params={"q": query, "limit": limit, "filter": "buyingOptions:{FIXED_PRICE}"},
            )
            r.raise_for_status()
            out: list[Listing] = []
            for it in r.json().get("itemSummaries", []):
                price = float(it.get("price", {}).get("value", 0) or 0)
                ship = 0.0
                opts = it.get("shippingOptions") or []
                if opts:
                    ship = float(opts[0].get("shippingCost", {}).get("value", 0) or 0)
                out.append(Listing(
                    listing_id=it.get("itemId", ""),
                    title=it.get("title", ""),
                    price=price, shipping=ship,
                    currency=it.get("price", {}).get("currency", "USD"),
                    url=it.get("itemWebUrl", ""),
                    location=(it.get("itemLocation") or {}).get("country", "US"),
                    fmt="BIN",
                ))
            return out


class SportsCardsProSource:
    """Sold-comp vendor (SportsCardsPro / PriceCharting backend).

    Skeleton: the request shape depends on your plan. Fill in the endpoint and
    map the response to a Comp. Returns None until wired so the pipeline safely
    skips rather than inventing a price.
    """
    BASE = "https://www.sportscardspro.com/api"

    def __init__(self, settings: Settings):
        self.s = settings

    def get_comp(self, card: Card) -> Optional[Comp]:
        if not self.s.price_vendor_api_key:
            return None
        # import httpx; query self.BASE with card fields; map graded vs raw;
        # build Comp(card_key=card.key(), median_sold=..., n=..., ...).
        return None


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------
def build_sources(settings: Settings) -> tuple[ListingSource, CompSource]:
    if settings.is_live:
        from grailbot import sample_data  # comps fallback if vendor=mock
        listing_src: ListingSource = EbayBrowseSource(settings)
        comp_src: CompSource = (
            SportsCardsProSource(settings)
            if settings.price_vendor in ("sportscardspro", "cardhedge")
            else MockCompSource(sample_data.SAMPLE_COMPS)
        )
        return listing_src, comp_src
    from grailbot import sample_data
    return (MockListingSource(sample_data.SAMPLE_LISTINGS),
            MockCompSource(sample_data.SAMPLE_COMPS))
