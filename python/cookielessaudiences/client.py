"""Client for the Cookieless Audiences API (https://www.cookielessaudiences.com)."""
from typing import Any, Dict, Iterable, List, Optional

import requests

__version__ = "1.0.0"
BASE = "https://www.cookielessaudiences.com"

STATUS_TEXT = {
    400: "Bad request, check the parameters",
    401: "Invalid API key",
    403: "Key not active or monthly credits used up",
    407: "Missing data_type, must be 'url' or 'text'",
    410: "Not enough content in the page or text",
    411: "The URL content could not be fetched",
    500: "General error, check the request or contact support",
}


class CookielessAudiencesError(Exception):
    """Raised when the JSON body carries a status other than 200."""

    def __init__(self, status: int, message: str, body: Optional[dict] = None):
        super().__init__("[%s] %s" % (status, message))
        self.status = status
        self.body = body or {}


class CookielessAudiences:
    def __init__(self, api_key: str, timeout: float = 120.0, session: Optional[requests.Session] = None):
        if not api_key:
            raise ValueError("An API key is required")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = "cookielessaudiences-python/%s (+https://www.cookielessaudiences.com)" % __version__

    def _post(self, path: str, form: Dict[str, str]) -> Dict[str, Any]:
        resp = self.session.post(BASE + path, data=form, timeout=self.timeout)
        try:
            body = resp.json()
        except ValueError:
            raise CookielessAudiencesError(resp.status_code, "Response was not JSON")
        status = body.get("status", 200) if isinstance(body, dict) else 200
        if status != 200:
            raise CookielessAudiencesError(status, STATUS_TEXT.get(status, "API error"), body)
        return body

    def segment(self, url: str, structured: bool = True) -> Dict[str, Any]:
        """Page-level audience segmentation. structured=False returns the legacy free-text shape."""
        form = {"query": url, "api_key": self.api_key}
        if structured:
            form["format"] = "structured"
        return self._post("/api/audience/segment.php", form)

    def categorize(self, url: str, confidence: bool = True, root_fallback: bool = False) -> Dict[str, Any]:
        """IAB content categorization (v3 and v2) of a URL."""
        form = {"query": url, "api_key": self.api_key, "data_type": "url"}
        if confidence:
            form["confidence"] = "1"
        if root_fallback:
            form["use_domain_as_basis_of_categorization_for_insufficient_subdomain_content"] = "1"
        return self._post("/api/iab/iab_web_content_filtering.php", form)

    def categorize_text(self, text: str, confidence: bool = True) -> Dict[str, Any]:
        """IAB content categorization of plain text."""
        form = {"query": text, "api_key": self.api_key, "data_type": "text"}
        if confidence:
            form["confidence"] = "1"
        return self._post("/api/iab/iab_content_filtering.php", form)

    def segment_many(self, urls: Iterable[str], workers: int = 8, structured: bool = True) -> Dict[str, Any]:
        """Segment several URLs in parallel. Returns {url: result or CookielessAudiencesError}."""
        from concurrent.futures import ThreadPoolExecutor

        urls = list(urls)

        def one(u: str):
            try:
                return self.segment(u, structured=structured)
            except Exception as exc:  # keep the batch going
                return exc

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            return dict(zip(urls, pool.map(one, urls)))

    @staticmethod
    def vocabularies(timeout: float = 60.0) -> Dict[str, Any]:
        """Controlled vocabularies, public, no key required."""
        resp = requests.get(BASE + "/api/audience/filters.php", timeout=timeout)
        resp.raise_for_status()
        return resp.json()


def labels_for(result: Dict[str, Any]) -> Dict[str, List[str]]:
    """Readable labels for the INT.* and PI.* codes of a structured response."""
    names = result.get("labels", {})
    out = {}
    for group in ("interests", "purchase_intent"):
        block = result.get(group) or {}
        codes = list(block.get("tier1", [])) + list(block.get("tier2", [])) + list(block.get("codes", []))
        out[group] = [names.get(c, c) for c in codes]
    return out
