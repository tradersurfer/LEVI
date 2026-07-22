import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import {
  applyAgentProgressEvent, beginAgentActivity, createAgentActivityState,
  mapConsensusStatus, markAgentActivityError,
} from '../src/lib/agentActivityAdapter.js'
import {
  AUTHENTICATED_STREAMING_UNAVAILABLE, GENERIC_STREAMING_FAILURE,
  streamingConnectionError,
} from '../src/lib/agentActivityConnection.js'

const completeAgents = ['SCRIBE', 'SCOUT', 'ATLAS', 'LENS', 'VOLT', 'GUARDIAN']
  .map(agentName => ({ agentName, status: 'complete' }))

test('guardian block takes precedence over false approval', () => {
  assert.equal(mapConsensusStatus({ approved: false, guardian_blocked: true }), 'blocked')
})

test('approved consensus maps to approved', () => {
  assert.equal(mapConsensusStatus({ approved: true, guardian_blocked: false }), 'approved')
})

test('completed run without approval maps to not approved', () => {
  assert.equal(mapConsensusStatus({ requestId: 'r1', agents: completeAgents, approved: false, guardian_blocked: false }), 'not_approved')
})

test('partial run maps to pending', () => {
  assert.equal(mapConsensusStatus({ requestId: 'r1', agents: [{ agentName: 'SCOUT', status: 'running' }] }), 'pending')
})

test('no run maps to idle', () => {
  assert.equal(mapConsensusStatus({}), 'idle')
})

test('connection failure maps to error', () => {
  assert.equal(mapConsensusStatus({ connectionError: true }), 'error')
})

test('authenticated WebSocket limitation has a specific honest message', () => {
  assert.equal(streamingConnectionError(true), AUTHENTICATED_STREAMING_UNAVAILABLE)
  assert.match(streamingConnectionError(true), /authenticated WebSockets, which aren't supported yet/)
})

test('ordinary WebSocket failure keeps a distinct generic message', () => {
  assert.equal(streamingConnectionError(false), GENERIC_STREAMING_FAILURE)
  assert.notEqual(streamingConnectionError(false), streamingConnectionError(true))
})

test('adapter preserves distinct final consensus fields', () => {
  const start = beginAgentActivity({ requestId: 'r1', symbol: 'spy' })
  const result = applyAgentProgressEvent(start, {
    request_id: 'r1', symbol: 'SPY', agent_name: 'CONSENSUS', status: 'blocked',
    approved: false, guardian_blocked: true, verdict: 'block', confidence: 0,
    summary: 'GUARDIAN veto',
  })
  assert.equal(result.consensus.status, 'blocked')
  assert.equal(result.consensus.approved, false)
  assert.equal(result.consensus.guardianBlocked, true)
})

test('adapter updates one canonical agent record', () => {
  const start = beginAgentActivity({ requestId: 'r1', symbol: 'SPY' })
  const result = applyAgentProgressEvent(start, {
    request_id: 'r1', symbol: 'SPY', agent_name: 'VOLT', status: 'complete',
    verdict: 'neutral', confidence: 1, summary: 'Calculated Greeks',
  })
  const volt = result.agents.find(agent => agent.agentName === 'VOLT')
  assert.equal(volt.summary, 'Calculated Greeks')
})

test('error adapter produces explicit error state', () => {
  assert.equal(markAgentActivityError(createAgentActivityState(), 'offline').consensus.status, 'error')
})

test('SCRIBE renders after Guardian and before final consensus', async () => {
  const source = await readFile(new URL('../src/components/agent-activity/AgentActivityPanel.jsx', import.meta.url), 'utf8')
  assert.ok(source.indexOf('<VotingCluster') < source.indexOf('<GuardianGate'))
  assert.ok(source.indexOf('<GuardianGate') < source.indexOf('levi-agent-stage--scribe'))
  assert.ok(source.indexOf('levi-agent-stage--scribe') < source.indexOf('<ConsensusBanner'))
})

test('SCRIBE is labelled as outcome narrative and ordered after guardian', async () => {
  const source = await readFile(new URL('../src/components/agent-activity/agentActivity.utils.js', import.meta.url), 'utf8')
  assert.match(source, /SCRIBE: \{ title: 'SCRIBE', role: 'Outcome narrative' \}/)
  assert.match(source, /'GUARDIAN', 'SCRIBE'/)
})

test('live page uses the single adapter and no raw event dump', async () => {
  const source = await readFile(new URL('../src/dev/AgentStreamPreview.jsx', import.meta.url), 'utf8')
  assert.match(source, /applyAgentProgressEvent/)
  assert.match(source, /<AgentActivityPanel/)
  assert.match(source, /config\.auth_enabled === true/)
  assert.match(source, /streamingConnectionError\(true\)/)
  assert.doesNotMatch(source, /<pre>/)
})

test('activity panel renders the stored connection error detail', async () => {
  const source = await readFile(new URL('../src/components/agent-activity/AgentActivityPanel.jsx', import.meta.url), 'utf8')
  assert.match(source, /<AgentActivityErrorState detail=\{consensus\.reason\}/)
})

test('mascot is served from dashboard public assets', async () => {
  const page = await readFile(new URL('../src/dev/AgentStreamPreview.jsx', import.meta.url), 'utf8')
  const mascot = await readFile(new URL('../public/assets/levi-avatar.svg', import.meta.url), 'utf8')
  assert.match(page, /\/assets\/levi-avatar\.svg/)
  assert.match(mascot, /<svg/)
})

test('activity design preserves reduced motion handling', async () => {
  const css = await readFile(new URL('../src/components/agent-activity/agentActivity.css', import.meta.url), 'utf8')
  assert.match(css, /prefers-reduced-motion: reduce/)
})
