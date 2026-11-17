import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, getSummary } from '../../api/client'
import { ErrorBanner, Loading } from '../../components/common'

function CountGroup({ title, counts, filterKey }) {
  const max = Math.max(1, ...Object.values(counts))
  return (
    <section className="card">
      <h2>{title}</h2>
      {Object.entries(counts).map(([name, n]) => (
        <Link key={name} to={`/support/queue?${filterKey}=${encodeURIComponent(name)}`} className="bar-row">
          <span className="bar-label">{name}</span>
          <span className="bar-track"><span className={`bar-fill ${filterKey}-${name.toLowerCase().replace(/\s+/g, '-')}`} style={{ width: `${(n / max) * 100}%` }} /></span>
          <span className="bar-value">{n}</span>
        </Link>
      ))}
    </section>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { getSummary().then(setSummary).catch((err) => setError(errorMessage(err))) }, [])

  if (error) return <ErrorBanner message={error} />
  if (!summary) return <Loading />

  return (
    <>
      <div className="kpis">
        <div className="kpi"><div className="kpi-value">{summary.total}</div><div className="muted">Total tickets</div></div>
        <div className="kpi"><div className="kpi-value">{summary.by_status['New']}</div><div className="muted">New</div></div>
        <div className="kpi"><div className="kpi-value">{summary.by_status['In Progress']}</div><div className="muted">In progress</div></div>
        <div className="kpi"><div className="kpi-value">{summary.by_priority['High']}</div><div className="muted">High priority</div></div>
      </div>
      <div className="grid-3">
        <CountGroup title="By status" counts={summary.by_status} filterKey="status" />
        <CountGroup title="By priority" counts={summary.by_priority} filterKey="priority" />
        <CountGroup title="By category" counts={summary.by_category} filterKey="category" />
      </div>
      <AIPerformance ai={summary.ai} />
    </>
  )
}

const rate = (v) => (v == null ? '—' : `${v}%`)

function AIPerformance({ ai }) {
  return (
    <section className="card ai-card">
      <div className="card-head">
        <h2>AI performance <span className="muted small">(from staff feedback)</span></h2>
        <span className="chip ai">Advisory only · staff confirm every value</span>
      </div>
      <div className="ai-stats">
        <div className="ai-stat"><div className="ai-stat-value">{ai.suggestions}</div><div className="muted">AI suggestions</div></div>
        <div className="ai-stat"><div className="ai-stat-value">{ai.tickets_analysed}</div><div className="muted">Tickets analysed</div></div>
        <div className="ai-stat"><div className="ai-stat-value">{ai.reviewed}</div><div className="muted">Reviewed by staff</div></div>
        <div className="ai-stat"><div className="ai-stat-value">{rate(ai.acceptance_rate)}</div><div className="muted">Accepted as-is</div></div>
        <div className="ai-stat"><div className="ai-stat-value">{rate(ai.useful_rate)}</div><div className="muted">Marked useful</div></div>
      </div>
      {ai.reviewed > 0 && (
        <div className="split-bar" title={`${ai.accepted} accepted, ${ai.corrected} corrected`}>
          <span className="split-accepted" style={{ flex: ai.accepted || 0.0001 }}>{ai.accepted} accepted</span>
          <span className="split-corrected" style={{ flex: ai.corrected || 0.0001 }}>{ai.corrected} corrected</span>
        </div>
      )}
      <p className="muted small">
        Every AI proposal is stored separately from the confirmed ticket values. Corrections show where the model
        needs a human — the AI never changes ticket status.
      </p>
    </section>
  )
}
