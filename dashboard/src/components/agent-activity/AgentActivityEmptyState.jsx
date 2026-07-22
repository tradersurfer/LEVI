export function AgentActivityEmptyState({ mascotSrc, message = 'Select a paper-trade setup to begin specialist analysis.' }) {
  return <section className="levi-agent-empty">
    {mascotSrc && <div className="levi-agent-empty__mascot"><img src={mascotSrc} alt="" aria-hidden="true" /></div>}
    <div className="levi-agent-empty__copy"><p className="levi-agent-empty__eyebrow">Live agent activity</p><h2>LEVI is standing by</h2><p>{message}</p></div>
  </section>
}
