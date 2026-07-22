import { useId } from 'react'
import { AgentNode } from './AgentNode'

export function GuardianGate({ agent }) {
  const titleId = useId()
  const isHardBlock = agent.status === 'blocked' || agent.verdict === 'block'
  return <section className={`levi-guardian-gate${isHardBlock ? ' levi-guardian-gate--blocked' : ''}`} aria-labelledby={titleId}>
    <div className="levi-guardian-gate__rail"><span>RISK GATE</span></div>
    <div className="levi-guardian-gate__content">
      <header className="levi-stage-heading">
        <div><p className="levi-stage-heading__eyebrow">Final enforcement layer</p><h2 id={titleId}>Guardian risk review</h2></div>
        <span className={`levi-guardian-gate__authority${isHardBlock ? ' levi-guardian-gate__authority--blocked' : ''}`}>Veto authority</span>
      </header>
      <AgentNode agent={agent} emphasized />
      {isHardBlock && <div className="levi-guardian-gate__block-notice" role="alert">
        <strong>Trade blocked by GUARDIAN</strong>
        <span>Directional agreement cannot override a deterministic risk violation.</span>
      </div>}
    </div>
  </section>
}
