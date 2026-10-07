"""Segment every URL in sites.txt and print one line per site."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from cookielessaudiences import CookielessAudiences

client = CookielessAudiences(os.environ["COOKIELESS_KEY"])
urls = [u.strip() for u in open("sites.txt") if u.strip()]
for url, res in client.segment_many(urls).items():
    print(url, "ERROR" if isinstance(res, Exception) else res.get("audience_type"))
