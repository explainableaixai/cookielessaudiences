'use strict';
const https = require('https');
const { URLSearchParams } = require('url');

const VERSION = '1.0.0';
const HOST = 'www.cookielessaudiences.com';

class CookielessAudiencesError extends Error {
  constructor(status, message, body) {
    super(message);
    this.name = 'CookielessAudiencesError';
    this.status = status;
    this.body = body;
  }
}

const ERRORS = {
  400: 'Bad request, check the parameters',
  401: 'Invalid API key',
  403: 'Key not active or monthly credits used up, check the account or buy more credits',
  407: 'Missing data_type, must be "url" or "text"',
  410: 'Not enough content in the page or text',
  411: 'The URL content could not be fetched',
  500: 'General error, check the request or contact support',
};

function request(method, path, form, timeout) {
  return new Promise((resolve, reject) => {
    const body = form ? new URLSearchParams(form).toString() : null;
    const headers = { 'User-Agent': `cookielessaudiences-node/${VERSION} (+https://www.cookielessaudiences.com)` };
    if (body) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
      headers['Content-Length'] = Buffer.byteLength(body);
    }
    const req = https.request({ host: HOST, path, method, headers, timeout }, (res) => {
      let data = '';
      res.setEncoding('utf8');
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        let json;
        try { json = JSON.parse(data); } catch (e) {
          return reject(new CookielessAudiencesError(res.statusCode, 'Response was not JSON', data));
        }
        resolve(json);
      });
    });
    req.on('timeout', () => req.destroy(new CookielessAudiencesError(0, 'Request timed out')));
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function check(json) {
  const status = json && typeof json.status === 'number' ? json.status : 200;
  if (status !== 200) {
    throw new CookielessAudiencesError(status, ERRORS[status] || `API returned status ${status}`, json);
  }
  return json;
}

class CookielessAudiences {
  constructor(apiKey, options = {}) {
    if (!apiKey) throw new Error('An API key is required');
    this.apiKey = apiKey;
    this.timeout = options.timeout || 120000;
  }

  /** Page-level audience segmentation. Pass structured=false for the legacy free-text shape. */
  async segment(url, { structured = true } = {}) {
    const form = { query: url, api_key: this.apiKey };
    if (structured) form.format = 'structured';
    return check(await request('POST', '/api/audience/segment.php', form, this.timeout));
  }

  /** IAB content categorization of a URL (v3 and v2 plus the filtering label). */
  async categorize(url, { confidence = true, rootFallback = false } = {}) {
    const form = { query: url, api_key: this.apiKey, data_type: 'url' };
    if (confidence) form.confidence = '1';
    if (rootFallback) form.use_domain_as_basis_of_categorization_for_insufficient_subdomain_content = '1';
    return check(await request('POST', '/api/iab/iab_web_content_filtering.php', form, this.timeout));
  }

  /** IAB content categorization of plain text. */
  async categorizeText(text, { confidence = true } = {}) {
    const form = { query: text, api_key: this.apiKey, data_type: 'text' };
    if (confidence) form.confidence = '1';
    return check(await request('POST', '/api/iab/iab_content_filtering.php', form, this.timeout));
  }

  /** Public vocabularies, no API key needed. */
  static async vocabularies(timeout = 60000) {
    return request('GET', '/api/audience/filters.php', null, timeout);
  }

  /** Map coded values (INT.*, PI.*) of a structured response to readable labels. */
  static labels(result) {
    const map = result.labels || {};
    const out = {};
    for (const group of ['interests', 'purchase_intent']) {
      const block = result[group] || {};
      const codes = [].concat(block.tier1 || [], block.tier2 || [], block.codes || []);
      out[group] = codes.map((c) => map[c] || c);
    }
    return out;
  }
}

module.exports = CookielessAudiences;
module.exports.CookielessAudiences = CookielessAudiences;
module.exports.CookielessAudiencesError = CookielessAudiencesError;
