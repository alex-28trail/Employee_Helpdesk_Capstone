import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  addComment, changeStatus, errorMessage, getHistory, getSuggestions, getTicket, updateTicket,
} from '../../api/client'
import { PRIORITIES, STATUSES, formatDate } from '../../constants'
import { Badge, ErrorBanner, History, Loading, Success } from '../../components/common'
import AIPanel from './AIPanel'

export default function SupportTicket() {
  const { id } = useParams()
  const [ticket, setTicket] = useState(null)
  const [history, setHistory] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [loadError, setLoadError] = useState('')

  const reload = useCallback(async () => {
    try {
      const [t, h, s] = await Promise.all([getTicket(id), getHistory(id), getSuggestions(id)])
      setTicket(t); setHistory(h); setSuggestions(s)
    } catch (err) {
      setLoadError(errorMessage(err))
    }
  }, [id])

  useEffect(() => { reload() }, [reload])

  if (loadError) return <section className="card"><ErrorBanner message={loadError} /><Link to="/support/queue">← Work queue</Link></section>
  if (!ticket) return <Loading />

  return (
    <div className="grid-2">
      <div>
        <section className="card">
          <Link to="/support/queue">← Work queue</Link>
          <h1>#{ticket.id} {ticket.title}</h1>
          <p className="muted">
            {ticket.requester?.name} · {ticket.requester?.department} · {ticket.requester?.email}
            <br />Raised {formatDate(ticket.created_at)} · Updated {formatDate(ticket.updated_at)}
          </p>
          <h3>Confirmed values</h3>
          <div className="meta-row">
            <Badge kind="status" value={ticket.status} />
            <Badge kind="priority" value={ticket.priority} />
            <span className="chip">{ticket.category}</span>
          </div>
          <h3>Description</h3>
          <p className="pre">{ticket.description}</p>
        </section>

        <ProcessingPanel ticket={ticket} onChange={reload} />
        <AIPanel ticket={ticket} suggestions={suggestions} onChange={reload} />
      </div>

      <section className="card">
        <h2>History</h2>
        <History items={history} />
      </section>
    </div>
  )
}

function ProcessingPanel({ ticket, onChange }) {
  const [status, setStatus] = useState(ticket.status)
  const [note, setNote] = useState('')
  const [priority, setPriority] = useState(ticket.priority)
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { setStatus(ticket.status); setPriority(ticket.priority) }, [ticket.status, ticket.priority])

  const run = async (fn, message) => {
    setBusy(true); setError(''); setOk('')
    try { await fn(); setOk(message); await onChange() } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <section className="card">
      <h2>Process ticket</h2>
      <ErrorBanner message={error} onClose={() => setError('')} />
      <Success message={ok} />

      <div className="form-row">
        <label>Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </label>
        <input placeholder="Optional note" value={note} onChange={(e) => setNote(e.target.value)} />
        <button className="btn primary" disabled={busy || status === ticket.status}
          onClick={() => run(async () => { await changeStatus(ticket.id, status, note); setNote('') }, `Status changed to ${status}.`)}>
          Update status
        </button>
      </div>
      <p className="muted small">Allowed: New → In Progress → Resolved, and Resolved → In Progress (reopen).</p>

      <div className="form-row">
        <label>Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </label>
        <button className="btn" disabled={busy || priority === ticket.priority}
          onClick={() => run(() => updateTicket(ticket.id, { priority }), `Priority set to ${priority}.`)}>
          Save priority
        </button>
      </div>

      <div className="field">
        <label htmlFor="comment">Add support comment</label>
        <textarea id="comment" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
      </div>
      <button className="btn" disabled={busy || !comment.trim()}
        onClick={() => run(async () => { await addComment(ticket.id, comment); setComment('') }, 'Comment added.')}>
        Add comment
      </button>
    </section>
  )
}
