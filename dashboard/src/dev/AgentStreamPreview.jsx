/*
 * DISPOSABLE PHASE 8 PROOF OF CONCEPT.
 * This unstyled dev-only view proves the wire protocol and is not production UI.
 */
import { useEffect, useRef, useState } from 'react'

const DEFAULT_USER = import.meta.env.VITE_LEVI_USER_ID || 'demo'
const API_BASE = import.meta.env.VITE_LEVI_API_BASE || 'http://localhost:8000'

export default function AgentStreamPreview() {
  const [userId, setUserId] = useState(DEFAULT_USER)
  const [symbol, setSymbol] = useState('SPY')
  const [events, setEvents] = useState([])
  const [requestId, setRequestId] = useState('')
  const socketRef = useRef(null)

  useEffect(() => () => socketRef.current?.close(), [])

  async function runAnalysis(event) {
    event.preventDefault()
    socketRef.current?.close()
    setEvents([])
    const websocketBase = API_BASE.replace(/^http/, 'ws')
    const socket = new WebSocket(`${websocketBase}/ws/agents?user_id=${encodeURIComponent(userId)}`)
    socketRef.current = socket
    socket.onmessage = ({ data }) => setEvents((current) => [...current, JSON.parse(data)])
    await new Promise((resolve, reject) => {
      socket.onopen = resolve
      socket.onerror = reject
    })
    const response = await fetch(`${API_BASE}/api/agents/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, symbol }),
    })
    const body = await response.json()
    if (!response.ok) throw new Error(body.detail || 'Analysis request failed')
    setRequestId(body.request_id)
  }

  return <main>
    <h1>Disposable agent stream preview</h1>
    <form onSubmit={runAnalysis}>
      <label>User <input value={userId} onChange={(event) => setUserId(event.target.value)} /></label>
      <label>Symbol <input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} /></label>
      <button type="submit">Run analysis</button>
    </form>
    <p>Request: {requestId || 'not started'}</p>
    <pre>{events.map((event) => JSON.stringify(event)).join('\n')}</pre>
  </main>
}
