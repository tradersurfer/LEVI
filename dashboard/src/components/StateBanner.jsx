export default function StateBanner({ report }) {
  if (!report) return <div className="state-banner"><span className="state-detail">Loading state…</span></div>

  const s = report.state || 'NORMAL'
  const lockLabels = {
    bias_neutral:    'BIAS NEUTRAL',
    block_puts:      'SHORTS LOCKED',
    min_dte_override: `DTE≥${report.locks?.min_dte_override} ONLY`,
    patience_matrix: 'PATIENCE MATRIX',
  }

  return (
    <div className="state-banner">
      <span className={`state-label chip chip-state-${s}`}>{s.replace('_', ' ')}</span>
      <div className="locks">
        {Object.entries(report.locks || {}).filter(([,v]) => v).map(([k]) => (
          <span key={k} className="chip chip-lock">{lockLabels[k] || k.toUpperCase()}</span>
        ))}
      </div>
      <span className="state-detail">
        {report.index} · last {report.last} · RSI15 {report.rsi15} ·
        gap {report.gap_pct > 0 ? '+' : ''}{report.gap_pct}% ·
        {report.above_vwap ? ' above' : ' BELOW'} VWAP {report.vwap}
      </span>
    </div>
  )
}
