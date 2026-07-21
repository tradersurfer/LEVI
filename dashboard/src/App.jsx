import { useState, useEffect, useCallback } from 'react'
import StateBanner from './components/StateBanner'
import AgentStrip from './components/AgentStrip'
import TierTable from './components/TierTable'
import TradesPanel from './components/TradesPanel'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [state,   setState]   = useState(null)
  const [signals, setSignals] = useState({})
  const [trades,  setTrades]  = useState({ open_trades: [], blocklist: [] })
  const [lastRefresh, setLastRefresh] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [s, sig, t] = await Promise.all([
        fetch(`${API}/state`).then(r => r.json()),
        fetch(`${API}/signals`).then(r => r.json()),
        fetch(`${API}/trades`).then(r => r.json()),
      ])
      setState(s); setSignals(sig); setTrades(t)
      setLastRefresh(new Date().toLocaleTimeString())
    } catch (e) {
      console.error('Refresh failed', e)
    }
  }, [])

  useEffect(() => {
    const initial = setTimeout(refresh, 0)
    const id = setInterval(refresh, 60_000)
    return () => {
      clearTimeout(initial)
      clearInterval(id)
    }
  }, [refresh])

  return (
    <div className="app">
      <header className="header">
        <span className="logo">JECI Trading Suite v2</span>
        <div className="header-right">
          {lastRefresh && <span className="refresh-ts">Last refresh {lastRefresh}</span>}
          <button className="btn-refresh" onClick={refresh}>↻ Refresh</button>
        </div>
      </header>
      <StateBanner report={state} />
      <AgentStrip />
      <section className="tiers">
        {['TRADERSURFER', 'ROBYHOOD', 'HODL'].map(tier => (
          <TierTable key={tier} tier={tier} signals={signals[tier] || []} />
        ))}
      </section>
      <TradesPanel trades={trades.open_trades} blocklist={trades.blocklist} />
    </div>
  )
}
