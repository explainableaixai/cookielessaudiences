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

<!--expanded-->
## Repository guide

This repository is the working home of the open client code for Cookieless Audiences. The `node/` folder holds the npm package and the `python/` folder holds the PyPI package. Both are small. They add three things to raw HTTP: form encoding where the service expects it, status handling where the service reports it, and a helper that turns coded values into readable labels.

If you only need one call, curl is enough. If you plan to call the service from production code, the clients save you from the three mistakes people make most: sending JSON to an endpoint that wants form fields, trusting the HTTP status instead of the body status, and showing raw codes to users.

## A closer look at the response

A structured response is built from blocks, and each block answers a question.

**Who are they?** `demographics` gives age brackets, gender skew, income level, education, life stage, household composition, employment status, home ownership and urbanicity. `b2b` gives company size band, seniority, job function and industry for business audiences.

**What do they care about?** `interests` holds codes in two tiers. Tier one is a group such as technology and computing. Tier two is a sub interest such as computing. There are 29 groups and 285 sub interests in the vocabulary.

**What might they buy?** `purchase_intent` holds codes from 34 groups and 283 segments, such as computer software or web hosting and cloud computing.

**Which named audiences fit?** `personas` lists personas with the mapping they came from. The dataset holds 1,667 deterministic personas.

**What kind of page is this?** `content_context` records the content type, the reading level and price signals.

**How sure is it?** Every block carries `confidence` as low, medium or high.

## Why fixed vocabularies matter

If a tool returns free text, two analysts looking at the same page can describe it in two ways, and a filter written last month can silently stop matching. With fixed vocabularies, a value means the same thing every time. A filter on `income_level = upper_middle` selects the same set of pages today and next quarter. A change to the vocabulary is announced by a version number in the response, and existing codes keep their meaning.

The vocabularies are published without a key at `/api/audience/filters.php`, so you can build forms, validators and dropdowns without calling the paid endpoints. A human readable version lives on the [audience segmentation taxonomy](https://www.cookielessaudiences.com/audience-segmentation-taxonomy.php) page.

## How teams plug it in

Some typical integration points:

- A planning tool calls `segment` when a user adds a site to a plan, and shows the audience beside the site.
- An inventory team runs a nightly job over new domains and tags each with codes.
- A data team enriches a warehouse table of referrer domains and joins the result onto sessions.
- A sales team ranks accounts by the B2B block before outreach.

In each case the integration is a thin function around one call and a table to store the answer. The clients here are meant to make that function boring.

## Choosing between the database and the API

The domain database holds pre-computed attributes for 120M domains, delivered as flat files with quarterly refreshes. It suits whole list work: curation, packaging, enrichment and market research. The real-time API suits cases where a single page matters. Both use the same vocabularies, so results line up across them.

Neither product is meant for the bidstream. They describe pages and domains for planning and analysis, and do not classify individual impressions.

## Related work from the same company

If you build products for people who hire, the [freelance platform vetting use case](https://www.resumereaderapi.com/use-cases/freelance-platforms.php) describes how parsed resumes give every applicant the same fields. If you advise buyers of companies, the [published sample screening reports](https://www.acquisitionuniverse.com/sample.php) show what evidence backed target screening looks like.

## Repository notes

The Node client is dependency free and runs on Node 14 or later. The Python client needs only `requests` and runs on Python 3.7 or later. Both are MIT licensed. Pull requests are welcome, and tests are expected with every change.

<!--extra-->
## Quick checklist for contributors

Run the package tests before you open a pull request. Add a test for every behaviour you change. Keep new code free of runtime dependencies in `node/` and limited to `requests` in `python/`. Update the README table if a method changes. Never commit keys or real responses that contain private data.

<!--further-->
## Further reading

The audience and content taxonomies behind the codes are maintained by the [IAB Tech Lab](https://iabtechlab.com/), whose standards pages describe the audience taxonomy, the content taxonomy and the seller defined audiences specification. Reading the audience taxonomy page alongside the field reference above makes the code names easier to follow, because the three branches of the standard map directly to the demographic, interest and purchase intent blocks of the response.

A practical note for anyone building on top of these clients: write your integration tests against the public vocabularies endpoint. It needs no key, costs nothing and fails loudly if a field you depend on changes.

## Support

Write to info@alpha-quantum.com for questions about plans or limits. Open an issue here for client bugs.

## Contributing

Issues and pull requests are welcome for the clients. Please keep new code free of runtime dependencies in `node/` and limited to `requests` in `python/`.

## Contact

info@alpha-quantum.com. Plans and the free vocabulary download are on [cookielessaudiences.com](https://www.cookielessaudiences.com/pricing.php).
