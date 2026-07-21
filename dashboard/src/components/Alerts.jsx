import EmptyState from './EmptyState'

export default function Alerts({ alerts = [] }) {
  return <section className="panel alerts" aria-labelledby="alerts-title"><p className="eyebrow">Notifications</p><h2 id="alerts-title">Alerts</h2>
    {alerts.length === 0 ? <EmptyState>No active alerts.</EmptyState> : alerts.map((alert, index) => <div className={`alert ${alert.severity || 'info'}`} key={alert.alert_id || index}><span className="alert-dot"/><div><strong>{alert.message}</strong><small>{alert.created_at || 'Just now'}</small></div></div>)}
  </section>
}
