import { useEffect, useState } from 'react'
import { BrowserRouter, Link, NavLink, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { getHealth, getRequesters } from './api/client'
import RaiseTicket from './pages/employee/RaiseTicket'
import MyTickets from './pages/employee/MyTickets'
import EmployeeTicketDetail from './pages/employee/TicketDetail'
import WorkQueue from './pages/support/WorkQueue'
import SupportTicket from './pages/support/SupportTicket'
import Dashboard from './pages/support/Dashboard'

const loadSaved = () => {
  try { return Number(localStorage.getItem('requesterId')) || null } catch { return null }
}

function HealthDot() {
  const [health, setHealth] = useState(null)
  useEffect(() => {
    const check = () => getHealth().then(setHealth).catch(() => setHealth({ status: 'down' }))
    check()
    const t = setInterval(check, 30000)
    return () => clearInterval(t)
  }, [])
  if (!health) return null
  const db = health.database?.status === 'ok'
  const ai = health.ai?.status === 'ok'
  const title = health.status === 'down' ? 'Backend not reachable' : `Database: ${health.database?.status}, AI: ${health.ai?.status}${health.ai?.detail ? ` (${health.ai.detail})` : ''}`
  return (
    <span className="health" title={title}>
      <span className={`dot ${health.status === 'down' ? 'bad' : db ? 'ok' : 'bad'}`} /> DB
      <span className={`dot ${ai ? 'ok' : 'bad'}`} /> AI
    </span>
  )
}

/* ---------- Landing: choose a portal ---------- */
function Landing() {
  return (
    <div className="landing">
      <div className="landing-inner">
        <div className="brand brand-dark">IT Helpdesk</div>
        <h1 className="landing-title">How can we help today?</h1>
        <p className="muted">Choose your portal to continue.</p>
        <div className="portal-cards">
          <Link to="/employee/new" className="portal-card portal-employee">
            <div className="portal-icon">👤</div>
            <h2>Employee Portal</h2>
            <p>Raise an IT ticket, track its progress and read updates from the support team.</p>
            <span className="portal-cta">Enter as employee →</span>
          </Link>
          <Link to="/support/queue" className="portal-card portal-support">
            <div className="portal-icon">🛠️</div>
            <h2>Support Team Portal</h2>
            <p>Triage the work queue, get AI recommendations, update status and see the dashboard.</p>
            <span className="portal-cta">Enter as support →</span>
          </Link>
        </div>
      </div>
    </div>
  )
}

/* ---------- Employee portal ---------- */
function EmployeeLayout({ requesters, requesterId, setRequesterId }) {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">IT Helpdesk</div>
        <div className="portal-tag">Employee Portal</div>
        <label className="acting">
          Signed in as
          <select value={requesterId || ''} onChange={(e) => setRequesterId(Number(e.target.value))}>
            {requesters.map((r) => (
              <option key={r.id} value={r.id}>{r.name} ({r.department})</option>
            ))}
          </select>
        </label>
        <nav>
          <NavLink to="/employee/new">Raise ticket</NavLink>
          <NavLink to="/employee/tickets">My tickets</NavLink>
        </nav>
        <div className="side-footer">
          <Link to="/" className="switch-portal">⇄ Switch portal</Link>
          <HealthDot />
        </div>
      </aside>
      <main className="container"><Outlet /></main>
    </div>
  )
}

/* ---------- Support portal ---------- */
function SupportLayout() {
  return (
    <div className="layout">
      <aside className="sidebar sidebar-support">
        <div className="brand">IT Helpdesk</div>
        <div className="portal-tag">Support Team Portal</div>
        <nav>
          <NavLink to="/support/queue">Work queue</NavLink>
          <NavLink to="/support/dashboard">Dashboard</NavLink>
        </nav>
        <div className="side-footer">
          <Link to="/" className="switch-portal">⇄ Switch portal</Link>
          <HealthDot />
        </div>
      </aside>
      <main className="container"><Outlet /></main>
    </div>
  )
}

export default function App() {
  const [requesters, setRequesters] = useState([])
  const [requesterId, setRequesterId] = useState(loadSaved)

  useEffect(() => {
    getRequesters()
      .then((list) => {
        setRequesters(list)
        if (!requesterId || !list.some((r) => r.id === requesterId)) setRequesterId(list[0]?.id ?? null)
      })
      .catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    try { if (requesterId) localStorage.setItem('requesterId', String(requesterId)) } catch { /* private mode */ }
  }, [requesterId])

  const me = requesters.find((r) => r.id === requesterId)

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />

        <Route path="/employee" element={
          <EmployeeLayout requesters={requesters} requesterId={requesterId} setRequesterId={setRequesterId} />
        }>
          <Route index element={<Navigate to="new" replace />} />
          <Route path="new" element={<RaiseTicket me={me} />} />
          <Route path="tickets" element={<MyTickets me={me} />} />
          <Route path="tickets/:id" element={<EmployeeTicketDetail />} />
        </Route>

        <Route path="/support" element={<SupportLayout />}>
          <Route index element={<Navigate to="queue" replace />} />
          <Route path="queue" element={<WorkQueue />} />
          <Route path="tickets/:id" element={<SupportTicket />} />
          <Route path="dashboard" element={<Dashboard />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
