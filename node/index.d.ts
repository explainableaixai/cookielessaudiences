export class CookielessAudiencesError extends Error {
  status: number;
  body?: unknown;
}
export interface SegmentOptions { structured?: boolean }
export interface CategorizeOptions { confidence?: boolean; rootFallback?: boolean }
export interface AudienceResult {
  url: string;
  vocab_version?: string;
  audience_type?: string;
  demographics?: Record<string, unknown>;
  b2b?: Record<string, unknown>;
  interests?: { tier1?: string[]; tier2?: string[]; confidence?: string };
  purchase_intent?: { codes?: string[]; confidence?: string };
  personas?: Array<{ persona: string; mapped_from?: string; source?: string }>;
  content_context?: Record<string, unknown>;
  labels?: Record<string, string>;
  status: number;
  [key: string]: unknown;
}
export class CookielessAudiences {
  constructor(apiKey: string, options?: { timeout?: number });
  segment(url: string, options?: SegmentOptions): Promise<AudienceResult>;
  categorize(url: string, options?: CategorizeOptions): Promise<Record<string, unknown>>;
  categorizeText(text: string, options?: { confidence?: boolean }): Promise<Record<string, unknown>>;
  static vocabularies(timeout?: number): Promise<Record<string, unknown>>;
  static labels(result: AudienceResult): { interests: string[]; purchase_intent: string[] };
}
export default CookielessAudiences;
