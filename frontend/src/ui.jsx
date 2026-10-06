import { Link, useLocation, useNavigate } from 'react-router-dom'
import { clearAuth, getUser } from './api'

export const Notice = ({ children }) => (
  <div className="bg-mist border border-line px-3 py-2 text-[11px] text-gray-600 flex gap-2"><span>ⓘ</span><span>{children}</span></div>
)
export const Stat = ({ label, value, sub, tone = 'ok' }) => (
  <div className="card p-3">
    <div className="lbl">{label}</div>
    <div className="text-2xl font-extrabold mt-1">{value ?? '—'}</div>
    {sub && <div className={`text-[10px] font-semibold ${tone === 'ok' ? 'text-ok' : tone === 'warn' ? 'text-warn' : 'text-bad'}`}>{sub}</div>}
  </div>
)
export const scoreColor = (s) => (s == null ? '#9CA3AF' : s >= 80 ? '#10B981' : s >= 65 ? '#F59E0B' : '#EF4444')
export const ScoreBar = ({ label, value, color }) => (
  <div className="mb-4">
    <div className="flex justify-between text-sm font-semibold"><span>{label}</span><span>{value ?? 'n/a'}{value != null && '/100'}</span></div>
    <div className="h-2 bg-mist mt-1.5"><div className="h-2" style={{ width: `${value ?? 0}%`, background: color || scoreColor(value) }} /></div>
  </div>
)
export const Section = ({ title, children, right }) => (
  <section className="mt-6"><div className="flex justify-between items-center mb-2"><div className="lbl">{title}</div>{right}</div>{children}</section>
)
export const mmss = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.round(s % 60)).padStart(2, '0')}`

export function Shell({ children, nav = true, wide = false }) {
  const loc = useLocation()
  const tabs = [['/dashboard', 'Dashboard'], ['/new', 'New analysis'], ['/progress', 'Progress'], ['/settings', 'Settings']]
  return (
    <div className="min-h-screen flex flex-col">
      {nav && (
        <header className="noprint bg-navy text-white">
          <div className="max-w-5xl mx-auto px-4 h-12 flex items-center justify-between">
            <Link to="/dashboard" className="text-xs font-extrabold tracking-[0.18em] uppercase">Silent Audience</Link>
            <nav className="flex gap-5">
              {tabs.map(([to, t]) => (
                <Link key={to} to={to} className={`text-[10px] font-bold uppercase tracking-[0.12em] ${loc.pathname === to ? 'text-white' : 'text-gray-400 hover:text-white'}`}>{t}</Link>
              ))}
            </nav>
          </div>
        </header>
      )}
      <main className={`flex-1 w-full mx-auto px-4 py-6 ${wide ? 'max-w-5xl' : 'max-w-4xl'}`}>{children}</main>
      <footer className="noprint bg-navy text-gray-400 text-[10px] px-4 py-4">
        <div className="max-w-5xl mx-auto">Videos, audio and slides are processed in a temporary directory and deleted right after analysis. Only metrics and AI feedback are stored.
          Eye-contact and engagement metrics are indicators, not absolute judgments, and may vary across cultures and disabilities.</div>
      </footer>
    </div>
  )
}
export const useLogout = () => { const n = useNavigate(); return () => { clearAuth(); n('/') } }
export const me = getUser
