import { useCallback, useEffect, useState } from 'react'
import { api, label, LOAN_TYPES, money, STAGES } from './api'

export default function App() {
  const [view, setView] = useState({ name: 'dashboard' })
  const [error, setError] = useState('')

  const go = (name, extra = {}) => { setError(''); setView({ name, ...extra }) }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1 className="brand">Broker<span>CRM</span></h1>
        <nav>
          <button className={view.name === 'dashboard' ? 'active' : ''} onClick={() => go('dashboard')}>Dashboard</button>
          <button className={['clients', 'client'].includes(view.name) ? 'active' : ''} onClick={() => go('clients')}>Clients</button>
          <button className={view.name === 'new' ? 'active' : ''} onClick={() => go('new')}>+ New client</button>
        </nav>
      </aside>
      <main className="content">
        {error && <div className="error" role="alert">{error}</div>}
        {view.name === 'dashboard' && <Dashboard onError={setError} onOpen={(id) => go('client', { id })} />}
        {view.name === 'clients' && <ClientList onError={setError} onOpen={(id) => go('client', { id })} />}
        {view.name === 'new' && <ClientForm onError={setError} onSaved={(c) => go('client', { id: c.id })} />}
        {view.name === 'client' && <ClientDetail id={view.id} onError={setError} onDeleted={() => go('clients')} />}
      </main>
    </div>
  )
}

function Dashboard({ onError, onOpen }) {
  const [data, setData] = useState(null)
  const [recent, setRecent] = useState([])

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => onError(e.message))
    api.listClients().then((c) => setRecent(c.slice(0, 5))).catch((e) => onError(e.message))
  }, [onError])

  if (!data) return <p className="muted">Loading…</p>
  const max = Math.max(1, ...data.by_stage.map((s) => s.count))

  return (
    <>
      <h2>Dashboard</h2>
      <div className="stats">
        <Stat title="Clients" value={data.total_clients} />
        <Stat title="Active pipeline" value={money(data.active_pipeline_amount)} />
        <Stat title="Settled" value={money(data.settled_amount)} />
        <Stat title="Open tasks" value={data.open_tasks} warn={data.overdue_tasks ? `${data.overdue_tasks} overdue` : ''} />
      </div>
      <div className="grid2">
        <section className="card">
          <h3>Pipeline by stage</h3>
          {data.by_stage.map((s) => (
            <div key={s.stage} className="bar-row">
              <span className="bar-label">{label(s.stage)}</span>
              <div className="bar"><div className={`bar-fill stage-${s.stage}`} style={{ width: `${(s.count / max) * 100}%` }} /></div>
              <span className="bar-value">{s.count} · {money(s.total_amount)}</span>
            </div>
          ))}
        </section>
        <section className="card">
          <h3>Recently updated</h3>
          {recent.length === 0 && <p className="muted">No clients yet.</p>}
          <ul className="list">
            {recent.map((c) => (
              <li key={c.id} onClick={() => onOpen(c.id)}>
                <strong>{c.full_name}</strong>
                <span className={`badge stage-${c.stage}`}>{label(c.stage)}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  )
}

function Stat({ title, value, warn }) {
  return (
    <div className="stat">
      <span className="muted">{title}</span>
      <strong>{value}</strong>
      {warn && <span className="warn">{warn}</span>}
    </div>
  )
}

function ClientList({ onError, onOpen }) {
  const [clients, setClients] = useState([])
  const [q, setQ] = useState('')
  const [stage, setStage] = useState('')

  useEffect(() => {
    const t = setTimeout(() => {
      api.listClients({ q, stage }).then(setClients).catch((e) => onError(e.message))
    }, 250)
    return () => clearTimeout(t)
  }, [q, stage, onError])

  return (
    <>
      <h2>Clients</h2>
      <div className="toolbar">
        <input placeholder="Search name, email or phone" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={stage} onChange={(e) => setStage(e.target.value)}>
          <option value="">All stages</option>
          {STAGES.map((s) => <option key={s} value={s}>{label(s)}</option>)}
        </select>
      </div>
      <table className="table">
        <thead><tr><th>Name</th><th>Loan</th><th>Amount</th><th>Stage</th><th>Lender</th></tr></thead>
        <tbody>
          {clients.map((c) => (
            <tr key={c.id} onClick={() => onOpen(c.id)}>
              <td><strong>{c.full_name}</strong><div className="muted small">{c.email}</div></td>
              <td>{label(c.loan_type)}</td>
              <td>{money(c.loan_amount)}</td>
              <td><span className={`badge stage-${c.stage}`}>{label(c.stage)}</span></td>
              <td>{c.lender || '—'}</td>
            </tr>
          ))}
          {clients.length === 0 && <tr><td colSpan="5" className="muted">No clients found.</td></tr>}
        </tbody>
      </table>
    </>
  )
}

function ClientForm({ onError, onSaved }) {
  const [form, setForm] = useState({ full_name: '', email: '', phone: '', loan_type: 'home_loan', loan_amount: '', stage: 'lead', lender: '' })
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const payload = { ...form, loan_amount: Number(form.loan_amount || 0) }
    for (const k of ['email', 'phone', 'lender']) if (!payload[k]) payload[k] = null
    try { onSaved(await api.createClient(payload)) } catch (err) { onError(err.message) }
  }

  return (
    <>
      <h2>New client</h2>
      <form className="card form" onSubmit={submit}>
        <label>Full name<input required value={form.full_name} onChange={set('full_name')} /></label>
        <label>Email<input type="email" value={form.email} onChange={set('email')} /></label>
        <label>Phone<input value={form.phone} onChange={set('phone')} /></label>
        <label>Loan type
          <select value={form.loan_type} onChange={set('loan_type')}>
            {LOAN_TYPES.map((t) => <option key={t} value={t}>{label(t)}</option>)}
          </select>
        </label>
        <label>Loan amount (AUD)<input type="number" min="0" required value={form.loan_amount} onChange={set('loan_amount')} /></label>
        <label>Stage
          <select value={form.stage} onChange={set('stage')}>
            {STAGES.map((s) => <option key={s} value={s}>{label(s)}</option>)}
          </select>
        </label>
        <label>Lender<input value={form.lender} onChange={set('lender')} /></label>
        <button className="primary" type="submit">Save client</button>
      </form>
    </>
  )
}

function ClientDetail({ id, onError, onDeleted }) {
  const [client, setClient] = useState(null)
  const [note, setNote] = useState('')
  const [task, setTask] = useState({ title: '', due_date: '' })
  const [ai, setAi] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [today] = useState(() => new Date().toISOString().slice(0, 10))

  const load = useCallback(() => api.getClient(id).then(setClient).catch((e) => onError(e.message)), [id, onError])
  useEffect(() => { load() }, [load])

  const run = (fn) => async (e) => {
    e?.preventDefault?.()
    try { await fn(); await load() } catch (err) { onError(err.message) }
  }

  if (!client) return <p className="muted">Loading…</p>

  return (
    <>
      <div className="detail-head">
        <div>
          <h2>{client.full_name}</h2>
          <p className="muted">{client.email || 'No email'} · {client.phone || 'No phone'}</p>
        </div>
        <button className="danger" onClick={run(async () => {
          if (confirm(`Delete ${client.full_name}?`)) { await api.deleteClient(id); onDeleted() }
        })}>Delete</button>
      </div>

      <div className="stats">
        <Stat title="Loan type" value={label(client.loan_type)} />
        <Stat title="Amount" value={money(client.loan_amount)} />
        <Stat title="Lender" value={client.lender || '—'} />
        <div className="stat">
          <span className="muted">Stage</span>
          <select value={client.stage} onChange={(e) => run(() => api.updateClient(id, { stage: e.target.value }))()}>
            {STAGES.map((s) => <option key={s} value={s}>{label(s)}</option>)}
          </select>
        </div>
      </div>

      <section className="card ai">
        <div className="ai-head">
          <h3>AI assistant</h3>
          <button className="primary" disabled={aiLoading} onClick={async () => {
            setAiLoading(true)
            try { setAi(await api.aiSummary(id)) } catch (e) { onError(e.message) } finally { setAiLoading(false) }
          }}>{aiLoading ? 'Thinking…' : 'Summarise & suggest next steps'}</button>
        </div>
        {ai && (
          <>
            <p>{ai.summary}</p>
            <ol>{ai.next_steps.map((s) => <li key={s}>{s}</li>)}</ol>
            <p className="muted small">Source: {ai.source === 'claude' ? 'Claude AI' : 'built-in rules (set ANTHROPIC_API_KEY to use Claude)'}</p>
          </>
        )}
      </section>

      <div className="grid2">
        <section className="card">
          <h3>Tasks</h3>
          <form className="inline" onSubmit={run(async () => {
            await api.addTask(id, { title: task.title, due_date: task.due_date || null }); setTask({ title: '', due_date: '' })
          })}>
            <input required placeholder="New task" value={task.title} onChange={(e) => setTask({ ...task, title: e.target.value })} />
            <input type="date" value={task.due_date} onChange={(e) => setTask({ ...task, due_date: e.target.value })} />
            <button type="submit">Add</button>
          </form>
          <ul className="list tasks">
            {client.tasks.map((t) => (
              <li key={t.id} className={t.done ? 'done' : t.due_date && t.due_date < today ? 'overdue' : ''}>
                <label>
                  <input type="checkbox" checked={t.done} onChange={run(() => api.updateTask(t.id, { done: !t.done }))} />
                  {t.title}
                </label>
                <span className="muted small">{t.due_date || ''}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h3>Notes</h3>
          <form className="inline" onSubmit={run(async () => { await api.addNote(id, note); setNote('') })}>
            <input required placeholder="Add a note" value={note} onChange={(e) => setNote(e.target.value)} />
            <button type="submit">Add</button>
          </form>
          <ul className="list notes">
            {client.notes.map((n) => (
              <li key={n.id}><span>{n.body}</span><span className="muted small">{new Date(n.created_at).toLocaleString('en-AU')}</span></li>
            ))}
          </ul>
        </section>
      </div>
    </>
  )
}
