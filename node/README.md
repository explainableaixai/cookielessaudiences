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

<!--expanded-->
## How the audience profile is built from a page

Most audience tools start with a person and end with a segment. This service starts with a page and ends with a description of the people that page attracts. The input is a URL. The output is a set of coded attributes with a confidence band on each block, so you always know how much weight a given answer deserves.

The attributes come from fixed, versioned vocabularies. Age is one of 8 brackets. Gender skew is a 5 point scale. Income has 6 bands, education has 7 levels, and life stage has 14 values such as young professional or family with young children. Interests are coded `INT.*` across 29 groups and 285 sub-interests. Purchase intent is coded `PI.*` across 34 groups and 283 segments. Because every value is enumerated, a filter you save today keeps working after the next vocabulary refresh.

Content predicts its own audience. A magazine about sailing sold advertising on who read it for a century without tracking a single subscriber. The API applies that old idea per URL. If you want the long form of the argument, the [cookieless audience segmentation guide](https://www.cookielessaudiences.com/features/cookieless-audience-segmentation.php) walks through the definition, the output and the activation paths.

## Reading confidence bands correctly

Every block returns `low`, `medium` or `high`. Treat the band as a routing rule in your code, not as decoration.

- **high**: safe to use as a hard filter in a media plan or a deal definition.
- **medium**: safe to use as a ranking signal, not as an exclusion.
- **low**: show it to a human, never automate a decision on it.

A block without evidence stays empty. That matters more than it sounds. A tool that fills every field makes your dashboards look complete and your decisions worse. An empty `b2b` block on a consumer recipe site is the correct answer, and your code should treat absence as information.

```js
function usable(block, minimum = 'medium') {
  const rank = { low: 1, medium: 2, high: 3 };
  return block && rank[block.confidence] >= rank[minimum];
}

const page = await client.segment(url);
if (usable(page.purchase_intent)) tagDeal(url, page.purchase_intent.codes);
```

## A caching strategy that saves credits

Pages change slowly. The audience of a news homepage does not flip between breakfast and lunch. That makes caching the cheapest quality improvement you can make.

1. Key the cache on the normalized URL, lowercased, without tracking parameters.
2. Store the whole response plus the `vocab_version`.
3. Expire entries after 7 to 30 days for editorial pages and 90 days for stable reference pages.
4. When the vocabulary version changes, mark old entries stale instead of deleting them, so you can diff the two answers.

For domain level questions, such as which sites in a list skew toward directors in data roles, the downloadable domain database is usually the better tool. It holds pre-computed attributes for 120M domains and is refreshed quarterly. The real-time API is for the moments when a single page matters more than its domain. The page on [audience personas for advertising](https://www.cookielessaudiences.com/features/audience-personas-advertising.php) explains the persona layer that sits on top of both.

## Migrating from cookie based segments

If your plans were built on third party cookie segments, you probably have a list of segment names in a spreadsheet and a set of campaigns that reference them. A migration does not need to be dramatic.

Start by mapping each old segment to a persona or to a pair of codes. "In market for SUVs" becomes a `PI.*` segment plus an income band. "Young professionals" becomes two life stages. Then run your top 200 domains through the API and compare the resulting audience to the old segment. Where they agree, switch the campaign. Where they disagree, you have just learned something about your old data.

Roughly 40 percent of web traffic is already cookieless, because Safari, Firefox and iOS block third party cookies by default. A plan that only sees Chrome with cookies is blind to a large slice of premium inventory. Profiling the property fixes that, because a site's audience does not vanish when the visitor arrives on an iPhone.

## Testing your integration without spending credits

Unit tests should never call the network. The client is a single class with one `request` function, so the simplest approach is to stub the module that talks to `https`:

```js
const https = require('https');
const { EventEmitter } = require('events');

function fakeResponse(json) {
  return (opts, cb) => {
    const res = new EventEmitter();
    res.setEncoding = () => {};
    process.nextTick(() => { cb(res); res.emit('data', JSON.stringify(json)); res.emit('end'); });
    const req = new EventEmitter();
    req.write = () => {}; req.end = () => {}; req.destroy = () => {};
    return req;
  };
}

https.request = fakeResponse({ status: 200, audience_type: 'consumer' });
```

For contract tests, call `CookielessAudiences.vocabularies()` once in CI. It needs no key and costs nothing. Assert that the field names you depend on, such as `age_bracket` and `income_level`, are still present.

## Where the same data shows up in other work

Audience attributes are useful well beyond ad planning. Teams that sell to businesses use the B2B block to rank accounts. The [account based profiling use case](https://www.cookielessaudiences.com/use-cases/abm-account-profiling.php) shows the idea: take the website of each account, read its firmographic bands, and sort.

Sibling products from the same company solve neighbouring problems. If your application also handles job applicants, the [resume parser](https://www.resumereaderapi.com/use-cases/recruitment-agencies.php) pages describe how candidate files become structured records for agencies. If your team evaluates companies as acquisition targets, the [company databases versus full web mapping guide](https://www.acquisitionuniverse.com/guides/company-databases-vs-full-web-mapping.php) explains a census style approach to building target lists.

## Troubleshooting

**Every call returns status 403.** The key is inactive or the monthly credits are gone. Check the account page before debugging code.

**Status 410 on a subdomain.** The subdomain has too little content. Call `categorize` with `rootFallback: true`, or pass the root domain.

**Status 411.** The page could not be fetched. Retry once, then skip it.

**Timeouts on large batches.** Lower your concurrency. The service handles about 270 URLs a minute at 50 parallel threads, and about 37 minutes per million URLs at 500 threads. Raise your limit gradually.

**Labels look different from last month.** Read `vocab_version` in the response. A new version can add codes. Existing codes keep their meaning.

## Glossary

- **Audience taxonomy**: the IAB Audience Taxonomy 1.1, which this service aligns with.
- **Persona**: a named audience such as Data Scientist, mapped from interests.
- **Seller defined audiences**: an IAB Tech Lab specification, released in 2022, for declaring audience segments in bid requests without exposing a user identity.
- **Vocabulary version**: the version of the enumerated lists behind the codes.
- **Confidence band**: low, medium or high, per block.

<!--further-->
## Further reading

Node developers who want to understand the platform features this client relies on, such as the HTTPS module, streams and timeouts, can start from the [Node.js documentation](https://nodejs.org/en). For the standard that the interest and purchase intent codes follow, the [IAB Tech Lab audience taxonomy](https://iabtechlab.com/standards/audience-taxonomy/) page describes the three branches of the taxonomy and how it is versioned.

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
