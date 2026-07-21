import EmptyState from './EmptyState'

export default function TradeJournal({ trades = [] }) {
  return <section className="panel" aria-labelledby="journal-title"><p className="eyebrow">Ledger</p><h2 id="journal-title">Trade journal</h2>
    {trades.length === 0 ? <EmptyState>No trades recorded.</EmptyState> : <div className="stack">{trades.map((trade, index) => <article className="row-card" key={trade.order_id || `${trade.symbol}-${index}`}><div><strong>{trade.symbol}</strong><span>{trade.side || trade.direction} · {trade.status}</span></div><div className="align-right"><strong className={Number(trade.pnl) >= 0 ? 'positive' : 'negative'}>{trade.pnl == null ? '—' : `$${Number(trade.pnl).toFixed(2)}`}</strong><span>{trade.reasoning || 'No rationale recorded'}</span></div></article>)}</div>}
  </section>
}
