const AGENTS = [
  { name: 'Grok',   role: 'Sentiment & Momentum',   schema: '{ sentiment_score: -1.0…1.0 }' },
  { name: 'Claude', role: 'Technical Chart Analyst', schema: '{ technical_bias: BUY|SELL|NEUTRAL }' },
  { name: 'DeepSeek', role: 'Chief Risk Officer',   schema: '{ verdict: APPROVED|REJECTED }' },
]

export default function AgentStrip() {
  return (
    <div className="agent-strip">
      {AGENTS.map(a => (
        <div key={a.name} className="agent-card">
          <div className="agent-name">{a.name}</div>
          <div className="agent-role">{a.role}</div>
          <div className="agent-schema">{a.schema}</div>
        </div>
      ))}
    </div>
  )
}
