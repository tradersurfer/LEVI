import { useId } from 'react'
import { AgentNode } from './AgentNode'
import { VotingCluster } from './VotingCluster'
import { GuardianGate } from './GuardianGate'
import { ConsensusBanner } from './ConsensusBanner'
import { AgentActivityEmptyState } from './AgentActivityEmptyState'
import { AgentActivityErrorState } from './AgentActivityErrorState'
import { getAgent, isActivityIdle } from './agentActivity.utils'
import './agentActivity.css'

export function AgentActivityPanel({
  agents, consensus, symbol, analysisLabel = 'Trade analysis', isConnected = true,
  isFixtureData = false, mascotSrc, emptyMessage, className,
}) {
  const titleId = useId()
  const idle = isActivityIdle(agents) && consensus.status === 'idle'
  const scribe = getAgent(agents, 'SCRIBE')
  const volt = getAgent(agents, 'VOLT')
  const guardian = getAgent(agents, 'GUARDIAN')

  return <section className={['levi-agent-activity', className || ''].filter(Boolean).join(' ')} aria-labelledby={titleId}>
    <header className="levi-agent-activity__header">
      <div><p className="levi-agent-activity__eyebrow">Live agent activity</p><div className="levi-agent-activity__title-row"><h1 id={titleId}>{analysisLabel}</h1>{symbol && <span className="levi-agent-activity__symbol">{symbol}</span>}</div></div>
      <div className="levi-agent-activity__connection"><span className={`levi-agent-activity__connection-dot levi-agent-activity__connection-dot--${isConnected ? 'connected' : 'offline'}`} aria-hidden="true" /><span>{isConnected ? 'Live stream connected' : 'Live stream unavailable'}</span></div>
    </header>
    {isFixtureData && <div className="levi-agent-activity__fixture-warning" role="status">Live API unavailable. Showing clearly labelled fixture data.</div>}
    {!isConnected && !isFixtureData ? <AgentActivityErrorState detail={consensus.reason} /> : idle ? <AgentActivityEmptyState mascotSrc={mascotSrc} message={emptyMessage} /> : <div className="levi-agent-activity__pipeline">
      <VotingCluster agents={agents} />
      <div className="levi-pipeline-connector" aria-hidden="true"><span /></div>
      <section className="levi-agent-stage levi-agent-stage--volt"><header className="levi-stage-heading"><div><p className="levi-stage-heading__eyebrow">Quantitative support</p><h2>Options mechanics</h2></div><span className="levi-stage-heading__rule">Deterministic</span></header><AgentNode agent={volt} /></section>
      <div className="levi-pipeline-connector" aria-hidden="true"><span /></div>
      <GuardianGate agent={guardian} />
      <div className="levi-pipeline-connector" aria-hidden="true"><span /></div>
      <section className="levi-agent-stage levi-agent-stage--scribe"><header className="levi-stage-heading"><div><p className="levi-stage-heading__eyebrow">Closing summary</p><h2>Outcome narrative</h2></div></header><AgentNode agent={scribe} /></section>
      <div className="levi-pipeline-connector levi-pipeline-connector--final" aria-hidden="true"><span /></div>
      <ConsensusBanner consensus={consensus} />
    </div>}
  </section>
}
