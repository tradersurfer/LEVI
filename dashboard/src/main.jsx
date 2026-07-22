import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import AgentStreamPreview from './dev/AgentStreamPreview.jsx'

const content = window.location.pathname === '/agent-activity' || (import.meta.env.DEV && window.location.pathname === '/dev/agent-stream')
  ? <AgentStreamPreview />
  : <App />

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {content}
  </StrictMode>,
)
