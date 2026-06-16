import { useState } from 'react'

const TIER_DESC = {
  TRADERSURFER: 'Master Swing Desk · $3–$20 prem · 3.29% cap',
  ROBYHOOD:     'Kids Sandbox · $150 hard cap · 4DTE min',
  HODL:         'Generational Trust · equity alerts only',
}

export default function TierTable({ tier, signals }) {
  const [open, setOpen] = useState(true)

  return (
    <div className="card">
      <div className="card-title" style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}
           onClick={() => setOpen(o => !o)}>
        <span>{tier}</span>
        <span style={{ color: 'var(--muted)' }}>{open ? '▾' : '▸'}</span>
      </div>
      <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 10 }}>{TIER_DESC[tier]}</div>
      {open && (
        signals.length === 0
          ? <div className="empty">No signals this cycle</div>
          : <table>
              <thead>
                <tr><th>Symbol</th><th>Dir</th><th>DTE</th><th>Prem</th><th>State</th><th>Time</th></tr>
              </thead>
              <tbody>
                {signals.map((s, i) => (
                  <tr key={i}>
                    <td>{s.symbol}</td>
                    <td><span className={`chip chip-${s.direction?.toLowerCase()}`}>{s.direction}</span></td>
                    <td>{s.dte}</td>
                    <td>${s.premium?.toFixed(2)}</td>
                    <td>{s.state}</td>
                    <td style={{ color: 'var(--muted)' }}>{s.timestamp ? new Date(s.timestamp).toLocaleTimeString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
      )}
    </div>
  )
}
