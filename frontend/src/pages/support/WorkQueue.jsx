import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { changeStatus, errorMessage, listTickets } from '../../api/client'
import { CATEGORIES, PRIORITIES, STATUSES, formatDate } from '../../constants'
import { Badge, ErrorBanner, Loading } from '../../components/common'

// One next step per status - same rules as the backend (routers/workflow.py), which still has the final say (409).
const NEXT_ACTION = {
  'New': { to: 'In Progress', label: 'Start work', className: 'action-start' },
  'In Progress': { to: 'Resolved', label: 'Mark resolved', className: 'action-resolve' },
  'Resolved': { to: 'In Progress', label: 'Reopen', className: 'action-reopen' },
}

/** Row action for support staff: a single, clearly labelled button for the allowed next status. */
function ActionCell({ ticket, onChanged }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const action = NEXT_ACTION[ticket.status]

  async function run() {
    setSaving(true); setError('')
    try {
      onChanged(await changeStatus(ticket.id, action.to))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="action-cell">
      <button className={`btn btn-sm action-btn ${action.className}`} onClick={run} disabled={saving}
        title={`Change status to ${action.to}`}>
        {saving ? 'Saving…' : action.label}
      </button>
      {error && <div className="row-error">{error}</div>}
    </div>
  )
}

export default function WorkQueue() {
  // Filters live in the URL so they survive refresh and the back button.
  const [params, setParams] = useSearchParams()
  const filters = {
    status: params.get('status') || '',
    category: params.get('category') || '',
    priority: params.get('priority') || '',
  }
  const [tickets, setTickets] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setTickets(null)
    listTickets(filters)
      .then(setTickets)
      .catch((err) => { setError(errorMessage(err)); setTickets([]) })
  }, [params.toString()]) // eslint-disable-line react-hooks/exhaustive-deps

  const setFilter = (key) => (e) => {
    const next = new URLSearchParams(params)
    if (e.target.value) next.set(key, e.target.value); else next.delete(key)
    setParams(next)
  }

  const Select = ({ name, options }) => (
    <label>
      {name}
      <select value={filters[name]} onChange={setFilter(name)}>
        <option value="">All</option>
        {options.map((o) => <option key={o}>{o}</option>)}
      </select>
    </label>
  )

  const replaceRow = (updated) => setTickets((rows) => rows.map((r) => (r.id === updated.id ? updated : r)))

  return (
    <section className="card">
      <div className="card-head">
        <h1>Work queue</h1>
        {tickets && <span className="muted small">{tickets.length} ticket{tickets.length === 1 ? '' : 's'}</span>}
      </div>
      <div className="filters">
        <Select name="status" options={STATUSES} />
        <Select name="category" options={CATEGORIES} />
        <Select name="priority" options={PRIORITIES} />
        {params.toString() && <button className="btn btn-sm" onClick={() => setParams({})}>Clear filters</button>}
      </div>
      <ErrorBanner message={error} />
      {!tickets ? <Loading /> : tickets.length === 0 ? <p className="muted">No tickets match these filters.</p> : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th><th>Title</th><th>Requester</th><th>Category</th>
                <th>Priority</th><th>Status</th><th>Created</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id}>
                  <td className="id-cell">#{t.id}</td>
                  <td className="title-cell"><Link to={`/support/tickets/${t.id}`}>{t.title}</Link></td>
                  <td>{t.requester?.name}<div className="muted small">{t.requester?.department}</div></td>
                  <td><span className="chip">{t.category}</span></td>
                  <td><Badge kind="priority" value={t.priority} /></td>
                  <td><Badge kind="status" value={t.status} /></td>
                  <td className="muted small">{formatDate(t.created_at)}</td>
                  <td><ActionCell ticket={t} onChanged={replaceRow} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
