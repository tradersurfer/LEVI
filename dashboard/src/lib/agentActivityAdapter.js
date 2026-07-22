import { AGENT_NAMES } from '../components/agent-activity/agentActivity.types.js'

const TERMINAL_STATUSES = new Set(['complete', 'blocked', 'error'])

export function mapConsensusStatus(payload = {}) {
  if (payload.guardian_blocked === true) return 'blocked'
  if (payload.approved === true) return 'approved'
  if (payload.connectionError === true || payload.status === 'error') return 'error'

  const agents = Array.isArray(payload.agents) ? payload.agents : []
  const hasRun = Boolean(payload.request_id || payload.requestId)
  if (!hasRun && agents.length === 0) return 'idle'

  const byName = new Map(agents.map((agent) => [agent.agentName, agent]))
  const allComplete = AGENT_NAMES.every((name) => TERMINAL_STATUSES.has(byName.get(name)?.status))
  if (allComplete) return 'not_approved'
  if (hasRun || agents.some((agent) => ['queued', 'running'].includes(agent.status))) return 'pending'
  return 'idle'
}

export function createAgentActivityState() {
  return {
    requestId: null,
    symbol: '',
    agents: [],
    consensus: {
      status: 'idle', approved: null, guardianBlocked: null,
      guardianClear: null, verdict: null, confidence: null,
      reason: null, voteLabel: 'Unanimous 3/3 required',
    },
    connectionError: false,
  }
}

export function beginAgentActivity({ requestId = 'starting', symbol }) {
  const agents = AGENT_NAMES.map((agentName) => ({
    agentName, status: 'idle', verdict: null, confidence: null, summary: null,
  }))
  return {
    ...createAgentActivityState(), requestId, symbol: symbol.toUpperCase(), agents,
    consensus: { ...createAgentActivityState().consensus, status: 'pending' },
  }
}

export function applyAgentProgressEvent(state, event) {
  if (!event || !event.agent_name) return state
  const next = {
    ...state,
    requestId: event.request_id || state.requestId,
    symbol: event.symbol || state.symbol,
    connectionError: false,
  }

  if (event.agent_name !== 'CONSENSUS') {
    const record = {
      agentName: event.agent_name,
      status: event.status,
      verdict: event.verdict ?? null,
      confidence: event.confidence ?? null,
      summary: event.summary ?? null,
    }
    const index = next.agents.findIndex((agent) => agent.agentName === record.agentName)
    next.agents = index === -1
      ? [...next.agents, record]
      : next.agents.map((agent, position) => position === index ? record : agent)
  }

  const approved = event.agent_name === 'CONSENSUS' && typeof event.approved === 'boolean'
    ? event.approved : next.consensus.approved
  const guardianBlocked = event.agent_name === 'CONSENSUS' && typeof event.guardian_blocked === 'boolean'
    ? event.guardian_blocked : next.consensus.guardianBlocked
  const status = mapConsensusStatus({
    requestId: next.requestId,
    agents: next.agents,
    approved,
    guardian_blocked: guardianBlocked,
    status: event.status,
  })
  next.consensus = {
    ...next.consensus,
    status,
    approved,
    guardianBlocked,
    guardianClear: guardianBlocked === null ? null : !guardianBlocked,
    verdict: event.agent_name === 'CONSENSUS' ? event.verdict : next.consensus.verdict,
    confidence: event.agent_name === 'CONSENSUS' ? event.confidence : next.consensus.confidence,
    reason: event.agent_name === 'CONSENSUS' ? event.summary : next.consensus.reason,
  }
  return next
}

export function markAgentActivityError(state, reason) {
  return {
    ...state,
    connectionError: true,
    consensus: { ...state.consensus, status: 'error', reason },
  }
}
