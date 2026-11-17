import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { errorMessage, getHistory, getTicket } from '../../api/client'
import { formatDate } from '../../constants'
import { Badge, ErrorBanner, History, Loading } from '../../components/common'

export default function EmployeeTicketDetail() {
  const { id } = useParams()
  const [ticket, setTicket] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getTicket(id), getHistory(id)])
      .then(([t, h]) => { setTicket(t); setHistory(h) })
      .catch((err) => setError(errorMessage(err)))
  }, [id])

  if (error) return <section className="card"><ErrorBanner message={error} /><Link to="/employee/tickets">← My tickets</Link></section>
  if (!ticket) return <Loading />

  // Employees see their own ticket's progress and support comments, not AI internals.
  const visible = history.filter((a) => !a.activity_type.startsWith('ai_'))
  const comments = history.filter((a) => a.activity_type === 'comment')

  return (
    <div className="grid-2">
      <section className="card">
        <Link to="/employee/tickets">← My tickets</Link>
        <h1>#{ticket.id} {ticket.title}</h1>
        <div className="meta-row">
          <Badge kind="status" value={ticket.status} />
          <Badge kind="priority" value={ticket.priority} />
          <span className="chip">{ticket.category}</span>
          <span className="muted">Raised {formatDate(ticket.created_at)}</span>
        </div>
        <h3>Description</h3>
        <p className="pre">{ticket.description}</p>

        <h3>Support comments</h3>
        {comments.length ? (
          <ul className="comments">
            {comments.map((c) => (
              <li key={c.id}><strong>{c.performed_by}</strong> <span className="muted">{formatDate(c.created_at)}</span><div>{c.description}</div></li>
            ))}
          </ul>
        ) : <p className="muted">No comments from support yet.</p>}
      </section>
      <section className="card">
        <h2>History</h2>
        <History items={visible} />
      </section>
    </div>
  )
}
