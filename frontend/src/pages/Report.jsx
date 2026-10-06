import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid, Legend } from 'recharts'
import { api } from '../api'
import { Shell, Notice, Stat, ScoreBar, Section, mmss, scoreColor } from '../ui'

const ICON = { strong: ['✦', 'text-ok'], insufficient: ['!', 'text-bad'], verbatim: ['▲', 'text-warn'], skipped: ['✕', 'text-bad'] }

function Presenter({ p }) {
  const m = p.metrics, sc = p.scores, cov = p.issues?.coverage || [], q = p.issues?.slide_quality
  const radar = [['Delivery', sc.delivery], ['Content', sc.coverage], ['Slides', sc.slides], ['Engagement', sc.engagement]].map(([k, v]) => ({ k, v: v ?? 0 }))
  const na = (v, f = (x) => x) => (v == null ? 'n/a' : f(v))
  return (
    <>
      <div className="flex items-center gap-3 mt-4">
        <div className="w-16 h-16 flex items-center justify-center text-2xl font-extrabold text-white" style={{ background: scoreColor(sc.overall) }}>{sc.overall}</div>
        <div><div className="lbl">Overall score</div><div className="text-lg font-extrabold">{p.name}</div></div>
      </div>
      <Section title="Performance breakdown">
        <div className="grid md:grid-cols-2 gap-4 card p-4">
          <div>
            <ScoreBar label="Delivery" value={sc.delivery} color="#0B1220" />
            <ScoreBar label="Content coverage" value={sc.coverage} color="#2563EB" />
            <ScoreBar label="Slide quality" value={sc.slides} color="#10B981" />
            <ScoreBar label="Engagement" value={sc.engagement} color="#F59E0B" />
          </div>
          <div className="h-52"><ResponsiveContainer><RadarChart data={radar}><PolarGrid /><PolarAngleAxis dataKey="k" tick={{ fontSize: 11 }} /><Radar dataKey="v" stroke="#0B1220" fill="#2563EB" fillOpacity={0.35} /></RadarChart></ResponsiveContainer></div>
        </div>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
        <Stat label="Pacing" value={`${m.wpm} WPM`} sub={m.wpm >= 120 && m.wpm <= 165 ? 'Optimal range' : 'Outside 120-165'} tone={m.wpm >= 120 && m.wpm <= 165 ? 'ok' : 'warn'} />
        <Stat label="Filler words" value={`${m.filler_total} total`} sub={`${m.filler_per_min} per min`} tone={m.filler_per_min > 3 ? 'warn' : 'ok'} />
        <Stat label="Eye contact" value={na(m.eye_contact_pct, (x) => x + '%')} sub={m.eye_contact_pct == null ? 'Vision not run' : 'Audience-facing'} tone="ok" />
        <Stat label="Monotone" value={na(m.monotone)} sub={m.pitch_std_hz ? `Pitch variation: ${m.pitch_std_hz}Hz` : 'Install librosa for pitch'} tone={m.monotone === 'High' ? 'bad' : 'ok'} />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
        <Stat label="Pauses" value={m.pause_count} sub={`avg ${m.avg_pause_s}s · max ${m.longest_pause_s}s`} />
        <Stat label="Repetitions" value={m.repetition_count} />
        <Stat label="Speaking time" value={mmss(m.speaking_seconds)} />
        <Stat label="Posture / hands" value={na(m.posture_score)} sub={m.hand_movement || ''} />
      </div>
      <Section title="Filler words & speaking pace over time">
        <div className="card p-3 h-60">
          {m.timeline?.length ? <ResponsiveContainer><LineChart data={m.timeline}><CartesianGrid stroke="#eee" /><XAxis dataKey="minute" tickFormatter={(v) => v + 'm'} fontSize={11} /><YAxis yAxisId="l" fontSize={11} /><YAxis yAxisId="r" orientation="right" fontSize={11} /><Tooltip /><Legend />
            <Line yAxisId="l" dataKey="fillers" name="Fillers" stroke="#EF4444" strokeWidth={2} /><Line yAxisId="r" dataKey="wpm" name="Pace (WPM)" stroke="#2563EB" strokeWidth={2} /></LineChart></ResponsiveContainer>
            : <div className="text-xs text-gray-500">No timeline available.</div>}
        </div>
      </Section>
      {m.slide_time?.length > 0 && (
        <Section title="Time per slide (seconds)">
          <div className="card p-3 h-52"><ResponsiveContainer><BarChart data={m.slide_time}><XAxis dataKey="slide" fontSize={11} tickFormatter={(v) => 'S' + v} /><YAxis fontSize={11} /><Tooltip /><Bar dataKey="seconds" fill="#0B1220" /></BarChart></ResponsiveContainer></div>
        </Section>
      )}
      {q && (
        <Section title="Slide quality">
          <div className="grid grid-cols-3 gap-3"><Stat label="Words / slide" value={q.avg_words_per_slide} sub={q.dense_slides?.length ? `Dense: ${q.dense_slides.join(', ')}` : 'Good density'} tone={q.dense_slides?.length ? 'warn' : 'ok'} /><Stat label="Readability" value={q.readability} sub="Flesch (higher = easier)" /><Stat label="Jargon density" value={q.jargon_density_pct + '%'} tone={q.jargon_density_pct > 15 ? 'warn' : 'ok'} /></div>
        </Section>
      )}
      {cov.length > 0 && (
        <Section title="Slide coverage analysis">
          <div className="card">{cov.map((c) => (
            <div key={c.slide} className="flex gap-3 px-3 py-2.5 border-b border-line last:border-0">
              <span className={`font-bold w-4 text-center ${ICON[c.status]?.[1]}`}>{ICON[c.status]?.[0]}</span>
              <div><div className="text-sm font-bold">Slide {c.slide}{c.title ? `: ${c.title}` : ''}</div><div className="text-[11px] text-gray-500">{c.note}</div></div>
            </div>))}</div>
          {p.issues?.skipped_topics?.length > 0 && <div className="text-xs text-gray-600 mt-2"><b>Topics skipped:</b> {p.issues.skipped_topics.join(', ')}</div>}
        </Section>
      )}
      <Section title="Personalised suggestions"><div className="card p-3 space-y-2">{p.suggestions.map((s, i) => <div key={i} className="text-sm flex gap-2"><span className="text-accent">→</span>{s}</div>)}</div></Section>
    </>
  )
}

function Team({ d, onRename, sid }) {
  const t = d.team, h = t.handoff
  const [edit, setEdit] = useState(false)
  const [map, setMap] = useState({})
  async function save() { await api(`/sessions/${sid}/speakers`, { method: 'PATCH', body: { mapping: map } }); setEdit(false); setMap({}); onRename() }
  return (
    <>
      <Section title="Team performance summary"><div className="card p-3 text-sm">{t.summary}</div></Section>
      <div className="grid grid-cols-2 gap-3 mt-3">
        <Stat label="Handoff smoothness" value={`${h.smoothness}/100`} sub={`Avg. ${h.avg_gap}s gap`} tone={h.smoothness >= 80 ? 'ok' : 'warn'} />
        <Stat label="Consistency" value={h.consistency} sub="Tone & style match" tone={h.consistency === 'HIGH' ? 'ok' : 'warn'} />
      </div>
      <Section title="Speaking time balance" right={<button className="lbl text-accent" onClick={() => setEdit(!edit)}>{edit ? 'Cancel' : 'Rename speakers'}</button>}>
        {edit && <div className="card p-3 mb-2 grid md:grid-cols-3 gap-2">{t.balance.map((b) => <input key={b.name} className="inp" placeholder={`Rename "${b.name}"`} onChange={(e) => setMap({ ...map, [b.name]: e.target.value })} />)}<button className="btn md:col-span-3" onClick={save}>Save names</button></div>}
        <div className="card p-3 h-44"><ResponsiveContainer><BarChart data={t.balance} layout="vertical"><XAxis type="number" hide /><YAxis type="category" dataKey="name" width={90} fontSize={12} /><Tooltip formatter={(v, n, p) => [`${mmss(v)} (${p.payload.pct}%)`, 'Time']} /><Bar dataKey="seconds" fill="#2563EB" /></BarChart></ResponsiveContainer></div>
      </Section>
      <Section title="Transition log"><div className="card">{h.transitions.map((x, i) => (
        <div key={i} className="flex justify-between px-3 py-2 border-b border-line last:border-0 text-sm"><span>{x.type === 'interruption' ? '⚠' : '⇄'} {x.from} → {x.to}{x.type === 'interruption' ? ' (interruption)' : ''}</span><span className="text-xs text-gray-500">{mmss(x.at)}</span></div>))}</div></Section>
      {h.plan?.length > 0 && <Section title="Team improvement plan"><div className="card p-3 bg-mist space-y-1">{h.plan.map((x, i) => <div key={i} className="text-xs">☐ {x}</div>)}</div></Section>}
      <div className="mt-3"><Notice>This report is supportive, not competitive. Scores are for each person's own growth.</Notice></div>
    </>
  )
}

export default function Report() {
  const { id } = useParams()
  const nav = useNavigate()
  const [d, setD] = useState(null)
  const [tab, setTab] = useState('team')
  const load = () => api(`/sessions/${id}`).then((r) => { setD(r); if (!r.team) setTab('0') })
  useEffect(() => { load() }, [id])
  if (!d) return <Shell wide><div className="text-sm text-gray-500">Loading…</div></Shell>
  const del = async () => { if (confirm('Delete this report permanently?')) { await api(`/sessions/${id}`, { method: 'DELETE' }); nav('/dashboard') } }
  const group = d.mode === 'group'
  return (
    <Shell wide>
      <div className="flex justify-between items-start">
        <div><div className="lbl">{group ? 'Team analysis report' : 'Session'} #{d.id}{d.is_mock ? ' · sample data' : ''}</div><h1 className="text-2xl font-extrabold">{d.title}</h1>
          <div className="mt-1 flex gap-2 text-[10px] font-bold uppercase"><span className="bg-navy text-white px-2 py-1">{group ? 'Group mode' : 'Individual'}</span><span className="text-gray-500 py-1">Persona: {d.persona}</span></div></div>
        <div className="noprint flex gap-2"><button className="btn2" onClick={() => window.print()}>Export PDF</button><button className="btn2 text-bad" onClick={del}>Delete</button></div>
      </div>
      {group && (
        <div className="noprint flex flex-wrap gap-2 mt-4">
          {d.team && <button onClick={() => setTab('team')} className={tab === 'team' ? 'btn' : 'btn2'}>Team report</button>}
          {d.presenters.map((p, i) => <button key={p.id} onClick={() => setTab(String(i))} className={tab === String(i) ? 'btn' : 'btn2'}>{p.name}</button>)}
        </div>
      )}
      {group && tab === 'team' && d.team ? <Team d={d} sid={id} onRename={load} /> : <Presenter p={d.presenters[Number(tab) || 0]} />}
      {d.questions.length > 0 && <div className="noprint mt-6"><Link to={`/qa/${d.id}`} className="btn inline-block">View simulated audience Q&A →</Link></div>}
      {d.transcript && <Section title="Transcript (saved with your consent)"><pre className="card p-3 text-xs whitespace-pre-wrap max-h-72 overflow-auto">{d.transcript}</pre></Section>}
      <div className="mt-6"><Notice>Eye-contact and engagement metrics are indicators, not absolute judgments, and may vary across cultures and disabilities.</Notice></div>
    </Shell>
  )
}
