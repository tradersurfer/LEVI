export default function ConsensusCard({ consensus = {} }) {
  return <div className={`consensus-card ${consensus.approved ? 'approved' : ''}`}>
    <span>Consensus</span><strong>{consensus.decision || 'not_approved'}</strong>
    <small>{consensus.votes_received || 0} / {consensus.votes_required || 3} votes</small>
  </div>
}
