import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, ResponsiveContainer, XAxis, Tooltip } from 'recharts'
import { api, getUser } from '../api'
import { Shell, Notice, scoreColor } from '../ui'

export default function Dashboard() {
  const [rows, setRows] = useState(null)
  const user = getUser()
  useEffect(() => { api('/sessions').then(setRows) }, [])
  const done = (rows || []).filter((r) => r.status === 'done')
  const avg = done.length ? (done.reduce((a, r) => a + r.overall_score, 0) / done.length).toFixed(1) : '—'
  const trend = [...done].reverse().map((r, i) => ({ n: i + 1, score: r.overall_score }))
  return (
    <Shell>
      <div className="lbl">Presentation hub</div>
      <h1 className="text-2xl font-extrabold">Welcome, {user?.name}</h1>
      <div className="grid grid-cols-2 gap-3 mt-5">
        <Link to="/new?mode=individual" className="card py-5 text-center hover:bg-mist"><div className="text-xl">👤</div><div className="lbl mt-1 text-navy">New individual</div></Link>
        <Link to="/new?mode=group" className="card py-5 text-center hover:bg-mist"><div className="text-xl">👥</div><div className="lbl mt-1 text-navy">New group</div></Link>
      </div>
      <div className="bg-navy text-white mt-3 p-4">
        <div className="lbl text-gray-400 text-center">Performance trend</div>
        <div className="h-28">
          {trend.length > 1 ? (
            <ResponsiveContainer><LineChart data={trend}><XAxis dataKey="n" hide /><Tooltip contentStyle={{ color: '#000', fontSize: 12 }} /><Line dataKey="score" stroke="#60A5FA" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer>
          ) : <div className="h-full flex items-center justify-center text-xs text-gray-400">Complete two analyses to see your trend</div>}
        </div>
        <div className="flex justify-between"><div><div className="text-[9px] text-gray-400">Avg. score</div><div className="text-2xl font-extrabold">{avg}</div></div>
          <div className="text-right"><div className="text-[9px] text-gray-400">Sessions</div><div className="text-2xl font-extrabold">{rows?.length ?? 0}</div></div></div>
      </div>
      <div className="lbl mt-6 mb-2">Recent analyses</div>
      {rows && rows.length === 0 && <div className="card p-6 text-sm text-gray-500 text-center">No sessions yet. Start a new individual or group analysis.</div>}
      {rows?.map((r) => (
        <Link key={r.id} to={r.status === 'done' ? `/report/${r.id}` : `/analysis/${r.id}`} className="card flex items-center justify-between p-3 mb-2 hover:bg-mist" style={{ borderLeft: `3px solid ${scoreColor(r.overall_score)}` }}>
          <div><div className="text-sm font-bold">{r.title}</div>
            <div className="text-[10px] text-gray-500">{new Date(r.created_at).toLocaleDateString()} · {r.mode === 'group' ? 'Group' : 'Individual'} · {r.persona}{r.is_mock ? ' · sample data' : ''}</div></div>
          <div className="text-right">{r.status === 'done' ? <><div className="text-sm font-extrabold">{r.overall_score}/100</div><div className="lbl">Overall</div></> : <div className={`lbl ${r.status === 'failed' ? 'text-bad' : ''}`}>{r.status}</div>}</div>
        </Link>
      ))}
      <div className="mt-4"><Notice>Videos and audio files are processed in a temporary directory and deleted immediately after analysis. We only store metrics and AI feedback.</Notice></div>
    </Shell>
  )
}
