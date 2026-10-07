# cookielessaudiences (Python)

Cookieless audience data for a URL, as a Python call. You pass a page and receive demographics, interests, purchase intent, B2B firmographics and personas, with no cookies and no personal data involved.

Built on `requests`, works on Python 3.7 and later.

## Setup

```bash
pip install cookielessaudiences
```

An API key comes with any plan. If you are still comparing options, read how [cookieless audience segmentation](https://www.cookielessaudiences.com/features/cookieless-audience-segmentation.php) works before you buy.

## Quick start

```python
from cookielessaudiences import CookielessAudiences, labels_for

client = CookielessAudiences("YOUR_API_KEY")
result = client.segment("https://example.com/blog")

print(result["audience_type"])
print(result["demographics"]["income_level"])
print(labels_for(result))
```

## Reading the response

Think of the structured result as five questions about the reader of a page:

1. Who are they? `demographics` and `b2b`
2. What do they like? `interests`, two tiers of `INT.*` codes
3. What might they buy? `purchase_intent`, `PI.*` codes
4. Which named audiences fit? `personas`
5. What kind of page is it? `content_context`

`labels_for(result)` turns the codes in questions 2 and 3 into names you can show to a person.

## API surface

```python
client.segment(url, structured=True)
client.categorize(url, confidence=True, root_fallback=False)
client.categorize_text(text, confidence=True)
client.segment_many(urls, workers=8)
CookielessAudiences.vocabularies()
```

`segment_many` returns a dict of url to result. A URL that failed holds its exception instead, so one bad page never stops a batch.

## Errors

```python
from cookielessaudiences import CookielessAudiencesError

try:
    client.segment(url)
except CookielessAudiencesError as exc:
    print(exc.status, exc.body)
```

The HTTP layer is plain; the signal lives in `status` inside the JSON. 401 is a bad key, 403 means the key is inactive or credits are gone, 410 and 411 mean the page could not be read.

## Example: audience report for a media plan

```python
import csv
from cookielessaudiences import CookielessAudiences, labels_for

client = CookielessAudiences("YOUR_API_KEY")
sites = [line.strip() for line in open("sites.txt") if line.strip()]
results = client.segment_many(sites, workers=10)

with open("plan.csv", "w", newline="") as fh:
    out = csv.writer(fh)
    out.writerow(["site", "type", "age", "income", "top_interest", "top_intent"])
    for site, res in results.items():
        if isinstance(res, Exception):
            out.writerow([site, "error", "", "", "", ""])
            continue
        names = labels_for(res)
        out.writerow([
            site,
            res.get("audience_type"),
            "|".join(res["demographics"].get("age_bracket", [])),
            res["demographics"].get("income_level"),
            (names["interests"] or [""])[0],
            (names["purchase_intent"] or [""])[0],
        ])
```

This is the shape most [website audience demographics](https://www.cookielessaudiences.com/features/website-audience-demographics.php) work takes: many sites in, one row per site out.

## Example: pandas enrichment

```python
import pandas as pd

df = pd.read_csv("accounts.csv")           # column: url
found = client.segment_many(df["url"].tolist())
df["audience_type"] = [r.get("audience_type") if isinstance(r, dict) else None for r in found.values()]
df["seniority"] = [
    ",".join(r.get("b2b", {}).get("seniority", [])) if isinstance(r, dict) else None
    for r in found.values()
]
```

## Example: IAB categories for a text snippet

```python
snippet = "Best budget laptops for students heading to university"
cats = client.categorize_text(snippet)
for name, score in cats["iab_classification"]:
    print(name, score)
```

## Frequently asked

**Can I get the full word list for a field?** Yes. `CookielessAudiences.vocabularies()` returns every enumerated value and needs no key.

**What about scale?** The service accepts up to 50 parallel threads by default, about 270 URLs a minute.

**Which fields are free text?** None in the structured shape. Small fields are closed lists; open-ended signals are mapped to canonical codes or dropped.

## Package notes

MIT licensed. Questions go to info@alpha-quantum.com. Version 1.0.0.
