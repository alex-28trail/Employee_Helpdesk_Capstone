import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, listTickets } from '../../api/client'
import { formatDate } from '../../constants'
import { Badge, ErrorBanner, Loading } from '../../components/common'

export default function MyTickets({ me }) {
  const [tickets, setTickets] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!me) return
    setTickets(null)
    listTickets({ requester_id: me.id })
      .then(setTickets)
      .catch((err) => { setError(errorMessage(err)); setTickets([]) })
  }, [me])

  return (
    <section className="card">
      <h1>My tickets</h1>
      <p className="muted">{me ? `${me.name} · ${me.department}` : ''}</p>
      <ErrorBanner message={error} />
      {!tickets ? <Loading /> : tickets.length === 0 ? (
        <p className="muted">No tickets yet. <Link to="/employee/new">Raise one</Link>.</p>
      ) : (
        <div className="table-wrap">
        <table className="table">
          <thead>
            <tr><th>ID</th><th>Title</th><th>Category</th><th>Priority</th><th>Status</th><th>Created</th></tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.id}>
                <td className="id-cell">#{t.id}</td>
                <td className="title-cell"><Link to={`/employee/tickets/${t.id}`}>{t.title}</Link></td>
                <td><span className="chip">{t.category}</span></td>
                <td><Badge kind="priority" value={t.priority} /></td>
                <td><Badge kind="status" value={t.status} /></td>
                <td className="muted small">{formatDate(t.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
    </section>
  )
}
