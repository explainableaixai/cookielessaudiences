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

<!--expanded-->
## Using the client in notebooks and pipelines

Analysts tend to meet this API in a notebook first, so it is worth showing a workflow that survives the trip from notebook to scheduled job. The goal is a table with one row per URL and one column per audience attribute, built once, cached on disk and refreshed on a schedule.

The structured response nests its blocks. Flatten it early, because everything downstream, from filters to charts, is easier on a flat frame:

```python
import pandas as pd

def flatten(url, res):
    d = res.get("demographics", {})
    b = res.get("b2b", {})
    return {
        "url": url,
        "audience_type": res.get("audience_type"),
        "age": ",".join(d.get("age_bracket", [])),
        "gender_skew": d.get("gender_skew"),
        "income": d.get("income_level"),
        "life_stage": ",".join(d.get("life_stage", [])),
        "seniority": ",".join(b.get("seniority", [])),
        "function": ",".join(b.get("job_function", [])),
        "interests": "|".join(res.get("interests", {}).get("tier1", [])),
        "intent": "|".join(res.get("purchase_intent", {}).get("codes", [])),
        "demo_confidence": d.get("confidence"),
    }

results = client.segment_many(urls, workers=10)
rows = [flatten(u, r) for u, r in results.items() if isinstance(r, dict)]
frame = pd.DataFrame(rows)
frame.to_parquet("audience.parquet")
```

Save the failures too. A URL that returned status 410 is a fact about that URL, and re-sending it every night wastes credits.

## What each field is good for

Think of the response as a questionnaire about the reader of a page. Each answer has a natural use.

| Field | Natural use |
|---|---|
| `audience_type` | split consumer, business and mixed sites before anything else |
| `age_bracket` | reach planning against 8 brackets |
| `gender_skew` | a 5 point scale, so use it as a tilt, not a hard rule |
| `income_level` | one of 6 bands, good for premium versus mass packages |
| `life_stage` | 14 stages, useful for lifecycle messaging |
| `interests` | tier 1 for grouping, tier 2 for precision |
| `purchase_intent` | the commercial angle, strongest evidence of fit for a campaign |
| `b2b` | seniority, job function and company size bands |
| `personas` | readable shorthand for planners |
| `content_context` | content type, reading level, price signals |

Purchase intent deserves special attention. It is the part of the profile closest to a buying decision, and the [purchase intent data](https://www.cookielessaudiences.com/features/purchase-intent-data.php) guide explains how the 283 segments are organised into 34 groups, so you can pick a level of detail that matches the size of your campaign.

## Scheduling and rate behaviour

A daily refresh of a few thousand URLs fits comfortably inside a cron job. Larger runs deserve more thought. The service handles roughly 270 URLs a minute at 50 parallel threads by default. A hundred thousand URLs take about six hours at that rate, and a million take about 37 minutes with 500 threads. Those numbers are a useful planning guide, but start small and watch your credit balance as you scale.

```python
# nightly.py, run from cron or an Airflow task
import json, pathlib
from cookielessaudiences import CookielessAudiences

client = CookielessAudiences(os.environ["COOKIELESS_KEY"])
seen = json.loads(pathlib.Path("seen.json").read_text()) if pathlib.Path("seen.json").exists() else {}
todo = [u for u in load_urls() if u not in seen]

for url, res in client.segment_many(todo[:5000], workers=12).items():
    seen[url] = {"error": res.status} if hasattr(res, "status") else res

pathlib.Path("seen.json").write_text(json.dumps(seen))
```

The cap of 5000 per run is a deliberate brake. It gives you a predictable daily spend and leaves room to investigate if something odd shows up in the failure counts.

## Quality checks worth automating

Because the output is coded, you can test it. Three checks catch most problems before a stakeholder does.

1. **Vocabulary membership.** Every code in `interests` and `purchase_intent` should exist in `CookielessAudiences.vocabularies()`. A code that does not is a bug in your mapping, not in the data.
2. **Distribution drift.** Compare the share of each `audience_type` this week against last week. A sudden swing usually means your URL list changed, not the web.
3. **Empty block rate.** If the rate of empty `purchase_intent` blocks jumps, inspect a sample of the URLs. Parked pages and login walls often explain it.

## Comparing the API with the domain database

Two products share one set of vocabularies. The API answers a question about a single page right now. The database holds pre-computed attributes for 120M domains and is delivered as files with quarterly refreshes. Pick the database when you work with whole lists offline, such as curating an inventory package or enriching a customer table. Pick the API when a specific article or product page matters.

Do not use either for impression level decisions in the bidstream. The service describes pages and domains for planning, curation and analysis. It is not a pre-bid classifier.

## Neighbouring use cases

Audience data helps in places you might not expect. Customer data platform teams join it onto referrer domains and account websites, as described in the [CDP enrichment use case](https://www.cookielessaudiences.com/use-cases/cdp-enrichment.php). If your pipeline also touches recruiting data, the [staffing agencies resume parsing page](https://www.resumereaderapi.com/use-cases/staffing-agencies.php) shows how candidate files become structured rows. If your analysts also size acquisition markets, the [published standards of Acquisition Universe](https://www.acquisitionuniverse.com/standards.php) show what a screening provider refuses to claim, which is a good template for your own data policies.

## Reproducibility notes

Pin the package version in `requirements.txt`. Record `vocab_version` next to every stored result. Write the date of each call. When you publish an analysis, a reader should be able to tell which vocabulary and which snapshot produced it. That discipline costs a few columns and saves arguments later.

## Privacy position

The service never uses cookies or user identifiers. It reads a page and describes the audience that page predictably attracts. No person is observed, so there is no consent flow to build around it, and the outputs carry no personal data.

## Notes on cost control

Credits are the one resource this API consumes, so it pays to treat them like a budget. Keep a running total in your job's log, compare it with the plan, and stop the run early if a ceiling is reached. Deduplicate URLs before sending them. Strip tracking parameters, since two URLs that differ only by a campaign tag describe the same page. Skip pages you already hold from the last thirty days. These three habits routinely remove a third of the calls in a real batch.

When you evaluate the service for the first time, resist the urge to send ten thousand URLs. Pick a hundred pages you know well, from five or six very different kinds of sites, and read the answers like an editor. Ask whether the age brackets match your own sense of the readership, whether the interests make sense, and whether the confidence bands are higher where you would expect. A hundred well chosen pages teach more than a hundred thousand random ones.

<!--further-->
## Further reading

The client uses only the `requests` library and the standard library, so the [Python documentation](https://docs.python.org/3/) covers everything under the hood, including `concurrent.futures`, which `segment_many` uses for its thread pool. On the content side, the [IAB content taxonomy](https://iabtechlab.com/standards/content-taxonomy/) is the standard behind the categorization endpoint, and its category names match what the API returns.

## Frequently asked

**Can I get the full word list for a field?** Yes. `CookielessAudiences.vocabularies()` returns every enumerated value and needs no key.

**What about scale?** The service accepts up to 50 parallel threads by default, about 270 URLs a minute.

**Which fields are free text?** None in the structured shape. Small fields are closed lists; open-ended signals are mapped to canonical codes or dropped.

## Package notes

MIT licensed. Questions go to info@alpha-quantum.com. Version 1.0.0.
