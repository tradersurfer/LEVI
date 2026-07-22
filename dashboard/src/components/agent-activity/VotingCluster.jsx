import { useId } from 'react'
import { AgentNode } from './AgentNode'
import { getAgent } from './agentActivity.utils'

export function VotingCluster({ agents }) {
  const titleId = useId()
  return <section className="levi-voting-cluster" aria-labelledby={titleId}>
    <header className="levi-stage-heading">
      <div><p className="levi-stage-heading__eyebrow">Directional intelligence</p><h2 id={titleId}>Independent voting agents</h2></div>
      <span className="levi-stage-heading__rule">Unanimous 3/3 required</span>
    </header>
    <div className="levi-voting-cluster__grid">
      <AgentNode agent={getAgent(agents, 'SCOUT')} />
      <AgentNode agent={getAgent(agents, 'ATLAS')} />
      <AgentNode agent={getAgent(agents, 'LENS')} />
    </div>
  </section>
}
