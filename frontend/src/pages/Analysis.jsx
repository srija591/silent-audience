import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { api } from '../api'
import { Shell, Notice } from '../ui'

export default function Analysis() {
  const { id } = useParams()
  const nav = useNavigate()
  const [s, setS] = useState(null)
  useEffect(() => {
    let stop = false
    const tick = async () => {
      try {
        const r = await api(`/sessions/${id}/status`)
        if (stop) return
        setS(r)
        if (r.status === 'done') return nav(`/report/${id}`, { replace: true })
        if (r.status === 'failed') return
      } catch {}
      setTimeout(tick, 1500)
    }
    tick()
    return () => { stop = true }
  }, [id])
  if (!s) return <Shell><div className="text-sm text-gray-500">Loading…</div></Shell>
  return (
    <Shell>
      <div className="text-center"><div className="lbl">Analyzing presentation</div><h1 className="text-xl font-extrabold">{s.title}</h1></div>
      <div className="card p-8 mt-5 text-center">
        {s.status === 'failed' ? (
          <><div className="text-bad font-bold">Analysis failed</div><div className="text-xs text-gray-600 mt-2 break-words">{s.error}</div>
            <div className="text-xs text-gray-500 mt-3">Check your SARVAM_API_KEY and the uploaded file, or set MOCK_MODE=true in backend/.env.</div>
            <Link to="/new" className="btn inline-block mt-4">Try again</Link></>
        ) : (
          <><div className="mx-auto w-16 h-16 rounded-full border-4 border-accent border-t-transparent animate-spin" />
            <div className="lbl text-accent mt-4">Processing pipeline · {s.progress}%</div>
            <div className="h-1.5 bg-mist mt-3 max-w-xs mx-auto"><div className="h-1.5 bg-accent transition-all" style={{ width: `${s.progress}%` }} /></div></>
        )}
      </div>
      <div className="card mt-4">
        {s.steps.map((t, i) => {
          const done = s.status === 'done' || i < s.step, cur = i === s.step && s.status === 'processing'
          return (
            <div key={t} className="flex items-center gap-3 px-4 py-3 border-b border-line last:border-0 text-sm">
              <span className={`w-5 h-5 flex items-center justify-center text-[11px] border ${done ? 'bg-ok border-ok text-white' : cur ? 'bg-accent border-accent text-white' : 'border-line text-gray-300'}`}>{done ? '✓' : cur ? '…' : ''}</span>
              <span className={done || cur ? 'font-semibold' : 'text-gray-400'}>{t}</span>
            </div>
          )
        })}
      </div>
      <div className="mt-4"><Notice>Eye-contact and engagement metrics are indicators, not absolute judgments, and may vary across cultures and disabilities.</Notice></div>
    </Shell>
  )
}
