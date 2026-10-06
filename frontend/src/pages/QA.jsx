import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { Shell, Notice } from '../ui'

export default function QA() {
  const { id } = useParams()
  const [d, setD] = useState(null)
  useEffect(() => { api(`/sessions/${id}`).then(setD) }, [id])
  if (!d) return <Shell><div className="text-sm text-gray-500">Loading…</div></Shell>
  return (
    <Shell>
      <div className="flex justify-between items-end"><div><div className="lbl text-accent">Simulated Q&A</div><h1 className="text-2xl font-extrabold">Audience: {d.persona} persona</h1></div>
        <Link to={`/report/${id}`} className="btn2 noprint">← Report</Link></div>
      <div className="mt-4"><Notice>The AI generated these questions from gaps in your talk. Expect tough questions on the topics below.</Notice></div>
      {d.questions.map((q, i) => (
        <div key={i} className="card p-4 mt-3">
          <div className="flex justify-between"><span className="bg-navy text-white text-[9px] font-bold uppercase px-2 py-1">Question {String(i + 1).padStart(2, '0')}</span><span className="lbl">{q.related_topic}</span></div>
          <div className="text-base font-bold mt-3">{q.question}</div>
          {q.rationale && <div className="text-[11px] text-gray-500 mt-2 border-t border-line pt-2">Rationale: {q.rationale}</div>}
        </div>
      ))}
      {d.questions.length === 0 && <div className="card p-6 mt-3 text-sm text-gray-500 text-center">Q&A generation was turned off for this session.</div>}
    </Shell>
  )
}
