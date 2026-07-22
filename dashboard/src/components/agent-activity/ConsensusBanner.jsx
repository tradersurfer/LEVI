import { formatConfidence, formatVerdict } from './agentActivity.utils'

const TITLES = {
  approved: 'Consensus approved', blocked: 'Trade blocked',
  not_approved: 'Consensus not reached', pending: 'Consensus pending',
  error: 'Consensus unavailable', idle: 'Awaiting analysis',
}

export function ConsensusBanner({ consensus }) {
  const title = TITLES[consensus.status] || TITLES.idle
  const hasConfidence = consensus.confidence !== null && consensus.confidence !== undefined
  const hasGuardian = consensus.guardianClear !== null && consensus.guardianClear !== undefined
  return <section className={`levi-consensus-banner levi-consensus-banner--${consensus.status}`} aria-live="polite" aria-label={title}>
    <div className="levi-consensus-banner__mark" aria-hidden="true" />
    <div className="levi-consensus-banner__content">
      <p className="levi-consensus-banner__eyebrow">Final system outcome</p>
      <div className="levi-consensus-banner__title-row">
        <h2>{title}</h2>
        {consensus.voteLabel && <span className="levi-consensus-banner__vote">{consensus.voteLabel}</span>}
      </div>
      <p className="levi-consensus-banner__reason">{consensus.reason || 'The final result will appear after all required agents complete.'}</p>
      <div className="levi-consensus-banner__metadata">
        {consensus.verdict && <span>Verdict <strong>{formatVerdict(consensus.verdict)}</strong></span>}
        {hasConfidence && <span>Confidence <strong>{formatConfidence(consensus.confidence)}</strong></span>}
        {hasGuardian && <span>Guardian <strong>{consensus.guardianClear ? 'Clear' : 'Blocked'}</strong></span>}
      </div>
    </div>
  </section>
}
