import ConsensusCard from './ConsensusCard'

export default function SpecialistPanel({ decisions = [], consensus = {} }) {
  return <section className="panel" aria-labelledby="specialist-title"><div className="panel-heading"><div><p className="eyebrow">Independent review</p><h2 id="specialist-title">Specialists</h2></div><ConsensusCard consensus={consensus} /></div>
    <div className="specialist-grid">{decisions.map(d => <article className="specialist" key={d.agent_name || d.agent}><div><strong>{d.agent_name || d.agent}</strong><span>{d.verdict || d.decision}</span></div><b>{Math.round(Number(d.confidence || 0) * 100)}%</b><p>{d.rationale || d.reasoning || 'No rationale available.'}</p></article>)}</div>
    <p className="fine-print">Consensus is display-only. The dashboard does not approve or execute trades.</p>
  </section>
}
