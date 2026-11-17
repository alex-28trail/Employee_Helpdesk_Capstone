import { formatDate } from '../constants'

const slug = (v) => String(v).toLowerCase().replace(/\s+/g, '-')

export function Badge({ value, kind }) {
  return <span className={`badge ${kind}-${slug(value)}`}>{value}</span>
}

export function ErrorBanner({ message, onClose }) {
  if (!message) return null
  return (
    <div className="alert alert-error" role="alert">
      <span>{message}</span>
      {onClose && <button className="link" onClick={onClose}>Dismiss</button>}
    </div>
  )
}

export function Success({ message }) {
  return message ? <div className="alert alert-success">{message}</div> : null
}

export function Loading({ text = 'Loading…' }) {
  return <p className="muted">{text}</p>
}

const ACTIVITY_LABEL = {
  created: 'Created',
  updated: 'Updated',
  status_change: 'Status',
  comment: 'Comment',
  ai_analysis: 'AI',
  ai_feedback: 'AI feedback',
}

export function History({ items }) {
  if (!items?.length) return <p className="muted">No activity yet.</p>
  return (
    <ol className="timeline">
      {items.map((a) => (
        <li key={a.id} className={`tl-${a.activity_type}`}>
          <div className="tl-head">
            <span className="tl-type">{ACTIVITY_LABEL[a.activity_type] || a.activity_type}</span>
            <span className="muted">{a.performed_by} · {formatDate(a.created_at)}</span>
          </div>
          {a.old_status || a.new_status ? (
            <div className="tl-status">
              {a.old_status && <><Badge kind="status" value={a.old_status} /> → </>}
              <Badge kind="status" value={a.new_status} />
            </div>
          ) : null}
          <div className="tl-body">{a.description}</div>
        </li>
      ))}
    </ol>
  )
}
