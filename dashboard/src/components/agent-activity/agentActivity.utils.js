export const AGENT_LABELS = Object.freeze({
  SCRIBE: { title: 'SCRIBE', role: 'Outcome narrative' },
  SCOUT: { title: 'SCOUT', role: 'Sentiment and flow' },
  ATLAS: { title: 'ATLAS', role: 'Macro regime' },
  LENS: { title: 'LENS', role: 'Technical structure' },
  VOLT: { title: 'VOLT', role: 'Greeks and volatility' },
  GUARDIAN: { title: 'GUARDIAN', role: 'Deterministic risk gate' },
})

export const AGENT_ORDER = Object.freeze([
  'SCOUT', 'ATLAS', 'LENS', 'VOLT', 'GUARDIAN', 'SCRIBE',
])

export const VOTING_AGENTS = Object.freeze(['SCOUT', 'ATLAS', 'LENS'])

export function normalizeConfidence(confidence) {
  if (confidence === null || confidence === undefined || Number.isNaN(confidence)) return null
  return Math.max(0, Math.min(1, confidence))
}

export function formatConfidence(confidence) {
  const normalized = normalizeConfidence(confidence)
  return normalized === null ? '—' : `${Math.round(normalized * 100)}%`
}

export function formatVerdict(verdict) {
  return verdict ? verdict.replaceAll('_', ' ') : 'Awaiting verdict'
}

export function formatStatus(status) {
  return ({
    idle: 'Idle', queued: 'Queued', running: 'Analyzing', complete: 'Complete',
    blocked: 'Blocked', error: 'Error',
  })[status] || 'Unknown'
}

export function getAgent(agents, agentName) {
  return agents.find((agent) => agent.agentName === agentName) || {
    agentName, status: 'idle', verdict: null, confidence: null, summary: null,
  }
}

export function isActivityIdle(agents) {
  return agents.length === 0 || agents.every((agent) => agent.status === 'idle')
}
