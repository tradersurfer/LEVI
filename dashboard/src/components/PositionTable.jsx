import EmptyState from './EmptyState'

export default function PositionTable({ positions = [] }) {
  if (positions.length === 0) return <EmptyState>No open positions.</EmptyState>
  return <div className="position-table" role="table" aria-label="Open positions">
    {positions.map((position, index) => <div className="position-row" role="row" key={position.symbol || index}>
      <strong role="cell">{position.symbol}</strong><span role="cell">Qty {position.quantity}</span>
      <span role="cell">Avg ${Number(position.average_price || 0).toFixed(2)}</span>
      <span role="cell" className={Number(position.unrealized_pnl) >= 0 ? 'positive' : 'negative'}>{Number(position.unrealized_pnl || 0).toFixed(2)} P&amp;L</span>
    </div>)}
  </div>
}
