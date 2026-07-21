export const fixtureDashboard = {
  summary: { display_name: 'Paper Trader', account_value: 25000, buying_power: 12000, daily_pnl: 184.25, realized_pnl: 74.25, unrealized_pnl: 110, open_positions: 1, execution_mode: 'paper_trading' },
  positions: { positions: [{ symbol: 'SPY 500C', quantity: 1, average_price: 2.35, current_price: 2.61, unrealized_pnl: 26 }] },
  trades: { trades: [{ symbol: 'SPY 500C', side: 'call', status: 'filled', fill_price: 2.35, pnl: 74.25, reasoning: 'Paper-only fixture: unanimous evidence review.' }] },
  evidence: { evidence: [{ evidence_id: 'fixture-chart', evidence_type: 'chart', source_name: 'Fixture', filename: 'spy-5m.png', ticker_symbols: ['SPY'], timeframe: '5m', confidence: 0.92, warnings: [] }] },
  decisions: {
    decisions: [
      { agent_name: 'SCOUT', verdict: 'approve', confidence: 0.84, rationale: 'Momentum evidence aligned.' },
      { agent_name: 'ATLAS', verdict: 'approve', confidence: 0.81, rationale: 'Macro regime supportive.' },
      { agent_name: 'LENS', verdict: 'approve', confidence: 0.86, rationale: 'Structure confirmed.' },
    ],
    consensus: { decision: 'approved', approved: true, votes_required: 3, votes_received: 3 },
  },
  alerts: { alerts: [{ alert_id: 'fixture-alert', severity: 'info', message: 'Paper order filled at 2.35', created_at: 'Fixture data' }] },
  setup_status: { complete: true, paper_trading: true, steps: [{ id: 'profile', label: 'Trading profile', complete: true }, { id: 'broker', label: 'Paper broker', complete: true }, { id: 'evidence', label: 'Evidence source', complete: true }] },
}
