import PositionTable from './PositionTable'

const money = value => Number(value || 0).toLocaleString(undefined, { style: 'currency', currency: 'USD' })

export default function StatePanel({ summary, positions = [] }) {
  const metrics = [['Account value', money(summary?.account_value)], ['Buying power', money(summary?.buying_power)], ['Daily P&L', money(summary?.daily_pnl)], ['Open positions', summary?.open_positions ?? positions.length]]
  return <section className="panel state-panel" aria-labelledby="state-title">
    <div className="panel-heading"><div><p className="eyebrow">Account state</p><h2 id="state-title">{summary?.display_name || 'LEVI workspace'}</h2></div><span className="mode">{summary?.execution_mode || 'paper_trading'}</span></div>
    <div className="metric-grid">{metrics.map(([label, value]) => <div className="metric" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
    <PositionTable positions={positions} />
  </section>
}
