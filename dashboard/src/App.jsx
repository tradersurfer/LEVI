import { useCallback, useEffect, useState } from 'react'
import { fetchDashboard } from './api/client'
import { fixtureDashboard } from './api/fixtures'
import Alerts from './components/Alerts'
import EvidenceViewer from './components/EvidenceViewer'
import SetupWizard from './components/SetupWizard'
import SpecialistPanel from './components/SpecialistPanel'
import StatePanel from './components/StatePanel'
import TradeJournal from './components/TradeJournal'
import ErrorState from './components/ErrorState'
import LoadingState from './components/LoadingState'
import './App.css'

const DEFAULT_USER = import.meta.env.VITE_LEVI_USER_ID || 'demo'

export default function App() {
  const [data, setData] = useState(fixtureDashboard)
  const [status, setStatus] = useState('fixture')
  const [updated, setUpdated] = useState(null)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setStatus('loading')
    try {
      setData(await fetchDashboard(DEFAULT_USER))
      setStatus('live')
      setError('')
      setUpdated(new Date().toLocaleTimeString())
    } catch {
      setData(fixtureDashboard)
      setStatus('fixture')
      setError('Live API unavailable. Showing clearly labelled fixture data.')
    }
  }, [])

  useEffect(() => {
    const initial = setTimeout(refresh, 0)
    const timer = setInterval(refresh, 60_000)
    return () => { clearTimeout(initial); clearInterval(timer) }
  }, [refresh])

  return <main className="app-shell">
    <header className="topbar">
      <div><span className="wordmark">LEVI</span><span className="product-name">Trading intelligence</span></div>
      <div className="top-actions"><span className={`connection ${status}`}>{status === 'live' ? 'Live API' : status === 'loading' ? 'Refreshing' : 'Fixture preview'}</span>{updated && <span className="timestamp">Updated {updated}</span>}<button onClick={refresh}>Refresh</button></div>
    </header>
    {status === 'loading' && <LoadingState />}
    {error && <ErrorState message={error} />}
    <div className="dashboard-grid">
      <div className="wide"><StatePanel summary={data.summary} positions={data.positions?.positions} /></div>
      <div className="span-8"><TradeJournal trades={data.trades?.trades} /></div>
      <div className="span-4"><Alerts alerts={data.alerts?.alerts} /></div>
      <div className="wide"><SpecialistPanel decisions={data.decisions?.decisions} consensus={data.decisions?.consensus} /></div>
      <div className="span-7"><EvidenceViewer evidence={data.evidence?.evidence} /></div>
      <div className="span-5"><SetupWizard setup={data.setup_status} /></div>
    </div>
    <footer>Paper trading by default · Evidence first · No automatic execution</footer>
  </main>
}
