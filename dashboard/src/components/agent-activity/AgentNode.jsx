import {
  AGENT_LABELS, formatConfidence, formatStatus, formatVerdict, normalizeConfidence,
} from './agentActivity.utils'

const WAITING_COPY = {
  idle: 'Waiting for analysis',
  queued: 'Queued for review',
}

export function AgentNode({ agent, compact = false, emphasized = false }) {
  const definition = AGENT_LABELS[agent.agentName]
  const confidence = normalizeConfidence(agent.confidence)
  const finished = agent.status === 'complete'

  return <article
    className={[
      'levi-agent-node', `levi-agent-node--${agent.status}`,
      agent.verdict ? `levi-agent-node--verdict-${agent.verdict}` : '',
      compact ? 'levi-agent-node--compact' : '',
      emphasized ? 'levi-agent-node--emphasized' : '',
    ].filter(Boolean).join(' ')}
    aria-label={`${definition.title}: ${formatStatus(agent.status)}`}
    data-agent={agent.agentName}
    data-status={agent.status}
    data-verdict={agent.verdict || 'none'}
  >
    <header className="levi-agent-node__header">
      <div className="levi-agent-node__identity">
        <span className="levi-agent-node__signal" aria-hidden="true">
          <span className="levi-agent-node__signal-core" />
        </span>
        <div>
          <h3 className="levi-agent-node__name">{definition.title}</h3>
          <p className="levi-agent-node__role">{definition.role}</p>
        </div>
      </div>
      <span className="levi-agent-node__status">{formatStatus(agent.status)}</span>
    </header>

    {agent.status === 'running' && <div className="levi-agent-node__activity" aria-label="Analysis in progress">
      <span /><span /><span /><span /><span />
    </div>}

    <div className="levi-agent-node__body">
      {WAITING_COPY[agent.status] ? <p className="levi-agent-node__placeholder">{WAITING_COPY[agent.status]}</p> : <>
        <div className="levi-agent-node__verdict-row">
          <span className="levi-agent-node__verdict">{formatVerdict(agent.verdict)}</span>
          {finished && confidence !== null && <span className="levi-agent-node__confidence">{formatConfidence(confidence)}</span>}
        </div>
        {finished && confidence !== null && <div className="levi-agent-node__confidence-track" aria-label={`Confidence ${formatConfidence(confidence)}`}>
          <span style={{ transform: `scaleX(${confidence})` }} />
        </div>}
        {agent.summary && <p className="levi-agent-node__summary">{agent.summary}</p>}
      </>}
    </div>
  </article>
}
