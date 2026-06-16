export default function TradesPanel({ trades, blocklist }) {
  return (
    <div className="card">
      <div className="card-title">Open Trades</div>
      {trades.length === 0
        ? <div className="empty">No open trades</div>
        : <table>
            <thead>
              <tr><th>Tier</th><th>Symbol</th><th>Dir</th><th>DTE</th><th>Entry $</th><th>Status</th></tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr key={i}>
                  <td>{t.tier}</td>
                  <td>{t.symbol}</td>
                  <td><span className={`chip chip-${t.direction?.toLowerCase()}`}>{t.direction}</span></td>
                  <td>{t.dte}</td>
                  <td>${t.premium?.toFixed(2) ?? t.entry?.toFixed(2)}</td>
                  <td>{t.status ?? 'open'}</td>
                </tr>
              ))}
            </tbody>
          </table>
      }
      {blocklist.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="card-title">Today's Blocklist (no re-entry)</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
            {blocklist.map(s => <span key={s} className="chip chip-lock">{s}</span>)}
          </div>
        </div>
      )}
    </div>
  )
}
