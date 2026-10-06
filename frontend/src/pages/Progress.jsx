import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts'
import { api } from '../api'
import { Shell } from '../ui'

const Delta = ({ v }) => (v == null ? <span className="text-gray-400">—</span> : <span className={`font-bold ${v > 0 ? 'text-ok' : v < 0 ? 'text-bad' : 'text-gray-500'}`}>{v > 0 ? '▲' : v < 0 ? '▼' : '='} {Math.abs(v)}</span>)

export default function Progress() {
  const [rows, setRows] = useState(null)
  useEffect(() => { api('/progress').then(setRows) }, [])
  const keys = [['overall', 'Overall'], ['delivery', 'Delivery'], ['coverage', 'Coverage'], ['slides', 'Slides'], ['engagement', 'Engagement']]
  return (
    <Shell wide>
      <div className="lbl">Individual mode</div><h1 className="text-2xl font-extrabold">Your progress over attempts</h1>
      {rows && rows.length < 2 && <div className="card p-6 mt-4 text-sm text-gray-500 text-center">Complete at least two individual analyses to compare attempts. <Link to="/new" className="underline">Start one</Link></div>}
      {rows?.length >= 2 && (
        <>
          <div className="card p-3 mt-4 h-64"><ResponsiveContainer><LineChart data={rows}><CartesianGrid stroke="#eee" /><XAxis dataKey="attempt" tickFormatter={(v) => 'Attempt ' + v} fontSize={11} /><YAxis domain={[0, 100]} fontSize={11} /><Tooltip /><Legend />
            <Line dataKey="overall" name="Overall" stroke="#0B1220" strokeWidth={2} /><Line dataKey="delivery" name="Delivery" stroke="#2563EB" /><Line dataKey="coverage" name="Coverage" stroke="#10B981" /><Line dataKey="engagement" name="Engagement" stroke="#F59E0B" /></LineChart></ResponsiveContainer></div>
          <div className="card mt-4 overflow-x-auto"><table className="w-full text-sm">
            <thead><tr className="lbl text-left border-b border-line"><th className="p-3">Attempt</th>{keys.map(([k, t]) => <th key={k} className="p-3">{t}</th>)}<th className="p-3">WPM</th><th className="p-3">Fillers/min</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.id} className="border-b border-line last:border-0"><td className="p-3"><Link to={`/report/${r.id}`} className="font-bold underline">#{r.attempt}</Link><div className="text-[10px] text-gray-500">{r.title}</div></td>
                {keys.map(([k]) => <td key={k} className="p-3"><div className="font-bold">{r[k] ?? '—'}</div>{r.delta && <Delta v={r.delta[k]} />}</td>)}
                <td className="p-3">{r.wpm}</td><td className="p-3">{r.filler_per_min}</td></tr>))}</tbody></table></div>
        </>
      )}
    </Shell>
  )
}
