/**
 * Presentational wire-contract vocabulary for live agent activity.
 * These constants mirror backend strings; they do not derive outcomes.
 */
export const AGENT_NAMES = Object.freeze([
  'SCRIBE', 'SCOUT', 'ATLAS', 'LENS', 'VOLT', 'GUARDIAN',
])

export const AGENT_STATUSES = Object.freeze([
  'idle', 'queued', 'running', 'complete', 'blocked', 'error',
])

export const AGENT_VERDICTS = Object.freeze([
  'bullish', 'bearish', 'neutral', 'block', 'insufficient_evidence',
])

export const CONSENSUS_STATUSES = Object.freeze([
  'idle', 'pending', 'approved', 'not_approved', 'blocked', 'error',
])
