export default function SetupWizard({ setup = {} }) {
  return <section className="panel" aria-labelledby="setup-title"><div className="panel-heading"><div><p className="eyebrow">Readiness</p><h2 id="setup-title">Setup wizard</h2></div><span className="mode">{setup.complete ? 'Ready' : 'Needs attention'}</span></div>
    <ol className="steps">{(setup.steps || []).map((step, index) => <li key={step.id} className={step.complete ? 'done' : ''}><b>{step.complete ? '✓' : index + 1}</b><span>{step.label}</span></li>)}</ol>
    <p className="fine-print">Broker credentials are configured outside this dashboard and are never displayed or stored here.</p>
  </section>
}
