# cookielessaudiences for Node.js

Page-level audience data for any URL, without a cookie or an identifier. Send a page, get back age brackets, income band, interests, purchase intent, B2B job functions and personas from fixed, versioned vocabularies.

Zero dependencies, Node 14 or newer, TypeScript types included.

## Install

```bash
npm install cookielessaudiences
```

You need an API key from a plan on the [audience segmentation API](https://www.cookielessaudiences.com/api.php) site. The same key works for audience segmentation and for IAB categorization.

## First call

```js
const CookielessAudiences = require('cookielessaudiences');

const client = new CookielessAudiences(process.env.COOKIELESS_KEY);
const page = await client.segment('https://example.com/blog');

console.log(page.audience_type);               // "b2b"
console.log(page.demographics.age_bracket);    // ["25_34", "35_44"]
console.log(CookielessAudiences.labels(page)); // readable interests and purchase intent
```

`segment()` asks for the structured response by default. Pass `{ structured: false }` if an older integration still expects the free-text shape.

## What a structured result contains

| Block | What you get |
|---|---|
| `audience_type` | consumer, b2b or mixed reading of the page |
| `demographics` | age brackets, gender skew, income level, education, life stage, household, employment, home ownership, urbanicity |
| `b2b` | company size band, seniority, job function, industry |
| `interests` | `INT.*` codes in two tiers |
| `purchase_intent` | `PI.*` segment codes |
| `personas` | named personas with the mapping they came from |
| `content_context` | content type, reading level, price signals |
| `labels` | code to readable name map for everything above |

Every block carries a `confidence` of low, medium or high. A page that does not support a block returns it empty instead of guessed.

## Methods

| Method | Endpoint | Returns |
|---|---|---|
| `segment(url, {structured})` | `/api/audience/segment.php` | audience profile |
| `categorize(url, {confidence, rootFallback})` | `/api/iab/iab_web_content_filtering.php` | IAB v3, IAB v2 and a filtering label |
| `categorizeText(text)` | `/api/iab/iab_content_filtering.php` | the same for pasted text |
| `CookielessAudiences.vocabularies()` | `/api/audience/filters.php` | every allowed value, no key needed |
| `CookielessAudiences.labels(result)` | local | readable interest and intent names |

Set `rootFallback: true` on `categorize()` when you pass subdomains that may be empty. The call then falls back to the root domain.

## Handling errors

The body carries a `status`. Anything other than 200 throws `CookielessAudiencesError` with `.status` and the raw `.body`.

```js
const { CookielessAudiencesError } = require('cookielessaudiences');

try {
  await client.segment(url);
} catch (err) {
  if (!(err instanceof CookielessAudiencesError)) throw err;
  if (err.status === 410 || err.status === 411) return null; // page had no readable content
  if (err.status === 403) throw new Error('Out of credits');
  throw err;
}
```

| Status | Meaning |
|---|---|
| 400 | check the parameters |
| 401 | invalid key |
| 403 | key not active or credits used up |
| 407 | missing `data_type` on IAB calls |
| 410 | not enough content |
| 411 | the page could not be fetched |
| 500 | general error |

## Recipe: enrich a publisher URL list with limited concurrency

```js
async function segmentAll(urls, limit = 8) {
  const out = new Map();
  const queue = [...urls];
  const workers = Array.from({ length: limit }, async () => {
    while (queue.length) {
      const url = queue.shift();
      try { out.set(url, await client.segment(url)); }
      catch (e) { out.set(url, { error: e.status || e.message }); }
    }
  });
  await Promise.all(workers);
  return out;
}
```

The service handles roughly 270 URLs a minute at 50 parallel threads, so a limit of 8 is a polite default for a first run.

## Recipe: build filter dropdowns from the vocabularies

```js
const vocab = await CookielessAudiences.vocabularies();
const ageOptions = vocab.fields.age_bracket;   // fixed list, safe to hard-wire into a UI
const interestGroups = Object.keys(vocab.interests);
```

Because values come from an enumerated list, a saved filter keeps working after a refresh. The human-readable version is the [audience taxonomy](https://www.cookielessaudiences.com/audience-segmentation-taxonomy.php) page.

## Recipe: route traffic by audience type

```js
app.use(async (req, res, next) => {
  const page = await client.segment(`https://${req.hostname}${req.originalUrl}`);
  res.locals.audience = page.audience_type;
  next();
});
```

Cache the result per URL. Pages change slowly, so a daily cache removes most of the cost.

## FAQ

### Does it set or read cookies?
No. Attributes are inferred from page content. There is no user tracking and no personal data in either direction.

### Is this for bidding?
No. Use it for planning, curation and analysis. It does not classify impressions in the bidstream.

### Which taxonomy does it follow?
Interests and purchase intent are aligned with the IAB Audience Taxonomy 1.1 and use `INT.*` and `PI.*` codes.

### Where do I check prices?
The [plans page](https://www.cookielessaudiences.com/pricing.php) lists the monthly API tiers and the downloadable domain database.

## License

MIT. Support: info@alpha-quantum.com
