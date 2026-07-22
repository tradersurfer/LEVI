export function AgentActivityErrorState({ message = 'Live activity is temporarily unavailable.', detail }) {
  return <section className="levi-agent-error" role="alert">
    <div className="levi-agent-error__icon" aria-hidden="true">!</div>
    <div><p className="levi-agent-error__eyebrow">Activity interruption</p><h2>{message}</h2><p>{detail || 'Existing account and journal data remain available. No agent result should be inferred while this panel is unavailable.'}</p></div>
  </section>
}
