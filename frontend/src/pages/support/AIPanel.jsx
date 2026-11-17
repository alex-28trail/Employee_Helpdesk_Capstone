import { useEffect, useState } from 'react'
import { errorMessage, runAnalysis, sendFeedback } from '../../api/client'
import { CATEGORIES, PRIORITIES, formatDate } from '../../constants'
import { Badge, ErrorBanner } from '../../components/common'

/** AI recommendation panel (F8.3) + feedback controls (F8.4).
 *  Suggested values are shown apart from the ticket's confirmed values and are never applied
 *  until a staff member accepts or corrects them. The AI cannot change status. */
export default function AIPanel({ ticket, suggestions, onChange }) {
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const latest = suggestions[0]

  async function analyse() {
    setRunning(true); setError('')
    try { await runAnalysis(ticket.id); await onChange() } catch (err) { setError(errorMessage(err)) } finally { setRunning(false) }
  }

  return (
    <section className="card ai-card">
      <div className="card-head">
        <h2>AI recommendation <span className="muted small">(advisory only)</span></h2>
        <button className="btn accent" onClick={analyse} disabled={running}>
          {running ? 'Analysing… (can take ~30s)' : latest ? 'Re-run analysis' : 'Run AI analysis'}
        </button>
      </div>

      {error && (
        <ErrorBanner message={`AI unavailable: ${error} The ticket was not changed — you can triage it manually.`}
          onClose={() => setError('')} />
      )}

      {!latest ? (
        <p className="muted">No AI analysis yet for this ticket.</p>
      ) : (
        <>
          <div className="compare">
            <div>
              <div className="label">AI suggests</div>
              <span className="chip ai">{latest.suggested_category}</span>{' '}
              <Badge kind="priority" value={latest.suggested_priority} />
            </div>
            <div>
              <div className="label">Confirmed on ticket</div>
              <span className="chip">{ticket.category}</span>{' '}
              <Badge kind="priority" value={ticket.priority} />
            </div>
          </div>
          <p><strong>Why this priority:</strong> {latest.priority_reason}</p>
          <strong>Troubleshooting steps</strong>
          <ol className="steps">{latest.troubleshooting_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
          <p className="muted small">Model {latest.model_name} · analysed {formatDate(latest.analyzed_at)}
            {latest.latency_ms ? ` · ${(latest.latency_ms / 1000).toFixed(1)}s` : ''}</p>

          {latest.feedback ? <FeedbackSummary fb={latest.feedback} /> : <FeedbackForm suggestion={latest} onDone={onChange} />}
        </>
      )}
    </section>
  )
}

function FeedbackSummary({ fb }) {
  return (
    <div className="alert alert-success">
      Staff <strong>{fb.decision}</strong> this suggestion · final {fb.final_category} / {fb.final_priority} ·
      marked <strong>{fb.useful ? 'useful' : 'not useful'}</strong> · {formatDate(fb.created_at)}
      {fb.comment && <div className="small">“{fb.comment}”</div>}
    </div>
  )
}

function FeedbackForm({ suggestion, onDone }) {
  const [useful, setUseful] = useState(true)
  const [correcting, setCorrecting] = useState(false)
  const [category, setCategory] = useState(suggestion.suggested_category)
  const [priority, setPriority] = useState(suggestion.suggested_priority)
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setCategory(suggestion.suggested_category); setPriority(suggestion.suggested_priority); setCorrecting(false)
  }, [suggestion.id]) // eslint-disable-line react-hooks/exhaustive-deps

  async function submit(decision) {
    setBusy(true); setError('')
    const body = { decision, useful, comment: comment || null }
    if (decision === 'corrected') Object.assign(body, { final_category: category, final_priority: priority })
    try { await sendFeedback(suggestion.id, body); await onDone() } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <div className="feedback">
      <h3>Your decision</h3>
      <ErrorBanner message={error} onClose={() => setError('')} />
      <div className="form-row">
        <span>Was this useful?</span>
        <label className="radio"><input type="radio" checked={useful} onChange={() => setUseful(true)} /> Useful</label>
        <label className="radio"><input type="radio" checked={!useful} onChange={() => setUseful(false)} /> Not useful</label>
      </div>

      {correcting && (
        <div className="form-row">
          <label>Final category
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
          <label>Final priority
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
            </select>
          </label>
        </div>
      )}
      <input className="full" placeholder="Optional comment" value={comment} onChange={(e) => setComment(e.target.value)} />

      <div className="form-row">
        {!correcting ? (
          <>
            <button className="btn primary" disabled={busy} onClick={() => submit('accepted')}>Accept suggestion</button>
            <button className="btn" disabled={busy} onClick={() => setCorrecting(true)}>Correct it…</button>
          </>
        ) : (
          <>
            <button className="btn primary" disabled={busy} onClick={() => submit('corrected')}>Save correction</button>
            <button className="btn" disabled={busy} onClick={() => setCorrecting(false)}>Cancel</button>
          </>
        )}
      </div>
    </div>
  )
}
