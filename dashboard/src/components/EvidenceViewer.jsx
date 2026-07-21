import EmptyState from './EmptyState'

export default function EvidenceViewer({ evidence = [] }) {
  return <section className="panel" aria-labelledby="evidence-title"><p className="eyebrow">Traceable inputs</p><h2 id="evidence-title">Evidence</h2>
    {evidence.length === 0 ? <EmptyState>No uploaded evidence.</EmptyState> : <div className="stack">{evidence.map(item => <article className="evidence-card" key={item.evidence_id}><div className="file-icon">{item.evidence_type?.slice(0, 2).toUpperCase()}</div><div><strong>{item.filename || item.evidence_type}</strong><span>{item.source_name} · {(item.ticker_symbols || []).join(', ') || 'No ticker'} · {item.timeframe || 'No timeframe'}</span><small>Confidence {Math.round(Number(item.confidence || 0) * 100)}%{item.warnings?.length ? ` · ${item.warnings.join('; ')}` : ''}</small></div></article>)}</div>}
  </section>
}
