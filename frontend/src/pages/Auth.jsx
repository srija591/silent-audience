import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setAuth } from '../api'
import { Shell, Notice } from '../ui'

const CAPS = [['Speech analysis', 'WPM, filler-word frequency, monotone detection and speaker diarization.'],
  ['Slide sync', 'Transcript-to-slide coverage analysis and jargon density scoring.'],
  ['Visual metrics', 'Eye-contact percentage and posture tracking (when enabled).'],
  ['Simulated Q&A', 'LLM-generated persona-based questions (Investor, Professor).']]

export default function Auth() {
  const [tab, setTab] = useState('signup')
  const [f, setF] = useState({ name: '', email: '', password: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  async function submit(e) {
    e.preventDefault(); setErr(''); setBusy(true)
    try {
      const r = await api(tab === 'signup' ? '/auth/signup' : '/auth/login', { method: 'POST', body: f })
      setAuth(r.token, r.user); nav('/dashboard')
    } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  return (
    <Shell nav={false}>
      <div className="lbl">AI Presentation Silent Audience</div>
      <h1 className="text-2xl md:text-3xl font-extrabold uppercase tracking-tight mt-1">Objective feedback for critical presentations</h1>
      <p className="text-sm text-gray-500 mt-1">Multi-modal analysis of speech, slides and body language.</p>
      <div className="grid grid-cols-2 border border-line mt-6">
        {[['signup', 'Create account'], ['login', 'Sign in']].map(([k, t]) => (
          <button key={k} onClick={() => setTab(k)} className={`py-2.5 text-[10px] font-bold uppercase tracking-[0.12em] ${tab === k ? 'bg-mist' : ''}`}>{t}</button>
        ))}
      </div>
      <form onSubmit={submit} className="border border-navy border-t-0 p-4 space-y-4">
        {tab === 'signup' && <div><div className="lbl mb-1">Full name</div><input className="inp" placeholder="John Doe" value={f.name} onChange={set('name')} required /></div>}
        <div><div className="lbl mb-1">Email address</div><input className="inp" type="email" placeholder="name@org.com" value={f.email} onChange={set('email')} required /></div>
        <div><div className="lbl mb-1">Password</div><input className="inp" type="password" placeholder="At least 6 characters" value={f.password} onChange={set('password')} required /></div>
        <Notice>Privacy notice: we do not store video, audio or slides permanently. Files are processed in a temporary directory and deleted immediately after analysis.</Notice>
        {err && <div className="text-xs text-bad font-semibold">{err}</div>}
        <button className="btn w-full" disabled={busy}>{busy ? 'Please wait…' : 'Proceed to dashboard'}</button>
      </form>
      <div className="lbl mt-8 pb-2 border-b border-line">System capabilities</div>
      <div className="grid md:grid-cols-2 gap-4 mt-4">
        {CAPS.map(([t, d]) => <div key={t}><div className="text-xs font-bold uppercase">{t}</div><div className="text-xs text-gray-500 mt-1">{d}</div></div>)}
      </div>
    </Shell>
  )
}
