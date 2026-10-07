# Cookieless Audiences: clients, examples and field reference

This repository is the home of the open client code for [Cookieless Audience Data](https://www.cookielessaudiences.com), a service that turns a web page into an audience profile without cookies, device IDs or personal data.

It holds the Node.js and Python clients side by side, runnable examples, and a plain-language reference for every field the API returns.

## Where to start

| You want to | Go to |
|---|---|
| call the API from JavaScript | `node/` |
| call the API from Python | `python/` |
| see real request and response shapes | `examples/` |
| understand each response field | the field reference below |
| try a plan | the pricing page linked at the end |

Other languages live in their own repositories: `cookielessaudiences-go`, `cookielessaudiences-dart` and `cookielessaudiences-rust`.

## Two products, one key

- Real-time API: send one URL, get a profile in the same request. Good when domain level data is too coarse.
- Domain database: pre-computed attributes for large domain lists, delivered as files. Good for planning, curation and enrichment offline.

Both use the same vocabularies, so a value in a database file means the same thing as a value in an API response.

## Quick call with curl

```bash
curl -X POST https://www.cookielessaudiences.com/api/audience/segment.php \
  -d 'query=https://example.com/blog' \
  -d 'api_key=YOUR_KEY' \
  -d 'format=structured'
```

A trimmed answer:

```json
{
  "audience_type": "b2b",
  "demographics": { "age_bracket": ["25_34", "35_44"], "income_level": "upper_middle" },
  "b2b": { "seniority": ["director", "senior_ic"], "job_function": ["data_analytics"] },
  "interests": { "tier1": ["INT.tech_computing"] },
  "purchase_intent": { "codes": ["PI.software.computer_software"] },
  "status": 200
}
```

## Field reference

| Field | Type | Values |
|---|---|---|
| `age_bracket` | list | 8 brackets |
| `gender_skew` | one value | 5 point scale from female to male lean |
| `income_level` | one value | 6 bands |
| `education_level` | one value | 7 levels |
| `life_stage` | list | 14 stages |
| `household_composition`, `employment_status`, `home_ownership`, `urbanicity` | one value | closed lists |
| `interests` | codes | 29 groups, 285 sub-interests |
| `purchase_intent` | codes | 34 groups, 283 segments |
| `b2b` | bands | company size, seniority, job function, industry |
| `personas` | list | named personas |
| `confidence` | per block | low, medium, high |

The full word lists are on the [audience segmentation taxonomy](https://www.cookielessaudiences.com/audience-segmentation-taxonomy.php) page and in JSON at `/api/audience/filters.php`.

## Why teams use it

Browsers that block third-party cookies already cover a large share of traffic, so identifier based planning loses reach every year. A profile built from the page itself works on every visit, in every browser.

Typical jobs:

- shortlist sites for a persona before a buy
- tag a curated package with interests and intent
- describe a publisher's audience in a pitch
- add audience context to accounts in a CDP
- check whether a site suits a brand

Each of these has its own page under [cookieless advertising solutions](https://www.cookielessaudiences.com/features/cookieless-advertising-solutions.php).

## Contextual vs behavioral in one paragraph

Behavioral targeting follows a person. Contextual targeting reads the page. This service reads the page and then describes who tends to be there, which is why it needs no consent flow. The longer argument is in the guide on [contextual vs behavioral targeting](https://www.cookielessaudiences.com/features/contextual-vs-behavioral-targeting.php).

## Error codes

| Status | Meaning |
|---|---|
| 200 | success |
| 400 | bad request |
| 401 | invalid key |
| 403 | key inactive or credits used up |
| 407 | `data_type` missing on IAB calls |
| 410 | not enough content |
| 411 | page could not be fetched |
| 500 | general error |

The HTTP code is not the signal. Always read `status` in the body.

## Repository layout

```
node/        npm package source (cookielessaudiences)
python/      PyPI package source (cookielessaudiences)
examples/    runnable scripts
LICENSE      MIT
```

## Contributing

Issues and pull requests are welcome for the clients. Please keep new code free of runtime dependencies in `node/` and limited to `requests` in `python/`.

## Contact

info@alpha-quantum.com. Plans and the free vocabulary download are on [cookielessaudiences.com](https://www.cookielessaudiences.com/pricing.php).
