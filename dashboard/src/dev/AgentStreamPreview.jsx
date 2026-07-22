import { useEffect, useRef, useState } from 'react'

import { AgentActivityPanel } from '../components/agent-activity'
import {
  applyAgentProgressEvent, beginAgentActivity, createAgentActivityState,
  markAgentActivityError,
} from '../lib/agentActivityAdapter'
import { streamingConnectionError } from '../lib/agentActivityConnection'

const DEFAULT_USER = import.meta.env.VITE_LEVI_USER_ID || 'demo'
const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_LEVI_API_BASE || 'http://localhost:8000'
const ACCESS_TOKEN = import.meta.env.VITE_LEVI_ACCESS_TOKEN || ''

export default function AgentStreamPreview() {
  const [userId, setUserId] = useState(DEFAULT_USER)
  const [symbol, setSymbol] = useState('SPY')
  const [activity, setActivity] = useState(createAgentActivityState)
  const [connected, setConnected] = useState(false)
  const socketRef = useRef(null)

  useEffect(() => {
    let disposed = false

    async function connect() {
      try {
        const configResponse = await fetch(`${API_BASE}/api/config`)
        if (!configResponse.ok) throw new Error('Runtime configuration is unavailable.')
        const config = await configResponse.json()
        if (disposed) return
        if (config.auth_enabled === true) {
          setConnected(false)
          setActivity((current) => markAgentActivityError(current, streamingConnectionError(true)))
          return
        }

        const websocketBase = API_BASE.replace(/^http/, 'ws')
        const socket = new WebSocket(`${websocketBase}/ws/agents?user_id=${encodeURIComponent(userId)}`)
        socketRef.current = socket
        socket.onopen = () => setConnected(true)
        socket.onmessage = ({ data }) => {
          try {
            setActivity((current) => applyAgentProgressEvent(current, JSON.parse(data)))
          } catch {
            setActivity((current) => markAgentActivityError(current, 'The activity stream returned invalid data.'))
          }
        }
        socket.onerror = () => {
          setConnected(false)
          setActivity((current) => markAgentActivityError(current, streamingConnectionError(false)))
        }
        socket.onclose = () => setConnected(false)
      } catch {
        if (!disposed) {
          setConnected(false)
          setActivity((current) => markAgentActivityError(current, streamingConnectionError(false)))
        }
      }
    }

    connect()
    return () => {
      disposed = true
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [userId])

  async function runAnalysis(event) {
    event.preventDefault()
    setActivity(beginAgentActivity({ symbol }))
    try {
      const response = await fetch(`${API_BASE}/api/agents/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(ACCESS_TOKEN ? { Authorization: `Bearer ${ACCESS_TOKEN}` } : {}),
        },
        body: JSON.stringify({ user_id: userId, symbol }),
      })
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail || 'Analysis request failed')
      setActivity((current) => ({ ...current, requestId: body.request_id }))
    } catch (error) {
      setActivity((current) => markAgentActivityError(current, error.message))
    }
  }

  return <main className="levi-agent-activity-page">
    <form className="levi-agent-activity-controls" onSubmit={runAnalysis}>
      <label>User <input value={userId} onChange={(event) => setUserId(event.target.value)} /></label>
      <label>Symbol <input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} /></label>
      <button type="submit" disabled={!connected}>Run analysis</button>
    </form>
    <AgentActivityPanel
      agents={activity.agents}
      consensus={activity.consensus}
      symbol={activity.symbol || symbol}
      analysisLabel="Specialist analysis"
      isConnected={connected || !activity.connectionError}
      mascotSrc="/assets/levi-avatar.svg"
    />
  </main>
}
