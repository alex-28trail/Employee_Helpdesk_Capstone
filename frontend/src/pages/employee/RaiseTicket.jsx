import { useState } from 'react'
import { Link } from 'react-router-dom'
import { createTicket, errorMessage, fieldErrors } from '../../api/client'
import { CATEGORIES } from '../../constants'
import { ErrorBanner } from '../../components/common'

const EMPTY = { title: '', description: '', category: 'Other' }

export default function RaiseTicket({ me }) {
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [banner, setBanner] = useState('')
  const [created, setCreated] = useState(null)
  const [saving, setSaving] = useState(false)

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setSaving(true); setErrors({}); setBanner(''); setCreated(null)
    try {
      // No client-side validation on purpose: FastAPI/Pydantic is the single source of truth (scenario 05).
      const ticket = await createTicket({ ...form, requester_id: me?.id })
      setCreated(ticket)
      setForm(EMPTY)
    } catch (err) {
      const fe = fieldErrors(err)
      setErrors(fe)
      if (!Object.keys(fe).length || fe.requester_id) setBanner(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="card narrow">
      <h1>Raise a ticket</h1>
      <p className="muted">Raising as <strong>{me ? `${me.name} · ${me.department}` : '…'}</strong></p>

      {created && (
        <div className="alert alert-success">
          Ticket #{created.id} created with status <strong>{created.status}</strong>.{' '}
          <Link to={`/employee/tickets/${created.id}`}>View ticket</Link>
        </div>
      )}
      <ErrorBanner message={banner} />

      <form onSubmit={submit} noValidate>
        <div className={`field ${errors.title ? 'has-error' : ''}`}>
          <label htmlFor="title">Title</label>
          <input id="title" value={form.title} onChange={set('title')} placeholder="e.g. Wireless keyboard not typing" />
          {errors.title && <div className="field-error">{errors.title}</div>}
        </div>

        <div className={`field ${errors.description ? 'has-error' : ''}`}>
          <label htmlFor="description">Description</label>
          <textarea id="description" rows={6} value={form.description} onChange={set('description')}
            placeholder="What happened, since when, how many people are affected, any workaround?" />
          {errors.description && <div className="field-error">{errors.description}</div>}
        </div>

        <div className={`field ${errors.category ? 'has-error' : ''}`}>
          <label htmlFor="category">Category (best guess)</label>
          <select id="category" value={form.category} onChange={set('category')}>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
          {errors.category && <div className="field-error">{errors.category}</div>}
        </div>

        <button className="btn primary" disabled={saving}>{saving ? 'Submitting…' : 'Submit ticket'}</button>
      </form>
    </section>
  )
}
