import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api, API_BASE } from '../api'
import { Shell, Notice } from '../ui'

const Toggle = ({ on, set, label }) => (
  <label className="flex items-center gap-3 text-sm cursor-pointer">
    <button type="button" onClick={() => set(!on)} className={`w-11 h-6 rounded-full p-0.5 transition ${on ? 'bg-navy' : 'bg-gray-300'}`}><span className={`block w-5 h-5 rounded-full bg-white transition ${on ? 'translate-x-5' : ''}`} /></button>{label}
  </label>
)
const Pick = ({ title, hint, file, setFile, accept, inputRef }) => (
  <div className="card p-3 flex items-center justify-between cursor-pointer hover:bg-mist" onClick={() => inputRef.current.click()}>
    <div><div className="text-sm font-bold">{title}</div><div className="text-[11px] text-gray-500">{file ? file.name : hint}</div></div>
    <span className="lbl text-navy">{file ? 'Change' : 'Upload'}</span>
    <input ref={inputRef} type="file" accept={accept} hidden onChange={(e) => setFile(e.target.files[0] || null)} />
  </div>
)

export default function NewAnalysis() {
  const [sp] = useSearchParams()
  const [mode, setMode] = useState(sp.get('mode') === 'group' ? 'group' : 'individual')
  const [media, setMedia] = useState(null), [slides, setSlides] = useState(null)
  const [title, setTitle] = useState(''), [persona, setPersona] = useState('Professor')
  const [store, setStore] = useState(false), [cv, setCv] = useState(true), [qa, setQa] = useState(true)
  const [names, setNames] = useState('Speaker 1, Speaker 2, Speaker 3')
  const [lang, setLang] = useState('en-IN')
  const [mock, setMock] = useState(true), [err, setErr] = useState(''), [busy, setBusy] = useState(false)
  const mRef = useRef(), sRef = useRef(), nav = useNavigate()
  useEffect(() => { fetch(API_BASE + '/api/health').then((r) => r.json()).then((h) => setMock(h.mock_mode)) }, [])

  async function start() {
    setErr('')
    if (!media && !mock) return setErr('Please upload a video or audio file.')
    const fd = new FormData()
    fd.append('mode', mode); fd.append('persona', persona); fd.append('title', title)
    fd.append('store_transcript', store); fd.append('enable_cv', cv); fd.append('enable_qa', qa)
    fd.append('language', lang)
    if (mode === 'group') fd.append('speaker_names', names)
    if (media) fd.append('media', media)
    if (slides) fd.append('slides', slides)
    setBusy(true)
    try { const r = await api('/sessions', { method: 'POST', body: fd }); nav(`/analysis/${r.id}`) }
    catch (x) { setErr(x.message); setBusy(false) }
  }
  const Opt = ({ k, t, d }) => (
    <button type="button" onClick={() => setMode(k)} className={`text-left p-3 border ${mode === k ? 'border-navy border-2' : 'border-line'}`}>
      <div className="flex justify-between"><span className="text-xs font-bold uppercase">{t}</span><span>{mode === k ? '◉' : '○'}</span></div><div className="text-[11px] text-gray-500 mt-1">{d}</div>
    </button>
  )
  return (
    <Shell>
      <div className="bg-navy text-white px-4 py-3"><div className="text-xs font-extrabold uppercase tracking-widest">Analysis configuration</div></div>
      {mock && <div className="mt-3"><Notice>Demo mode is on (no Sarvam API key). Uploading is optional and results are sample data so you can try the full flow.</Notice></div>}
      <div className="lbl mt-5 mb-2">01 · Analysis mode</div>
      <div className="grid md:grid-cols-2 gap-3">
        <Opt k="individual" t="Individual" d="Single presenter progress tracking and personal report." />
        <Opt k="group" t="Group" d="Multi-speaker diarization and team performance metrics." />
      </div>
      {mode === 'group' && <div className="mt-3"><div className="lbl mb-1">Presenter names (comma separated, you can rename later)</div><input className="inp" value={names} onChange={(e) => setNames(e.target.value)} /></div>}
      <div className="lbl mt-6 mb-2">02 · Data ingestion</div>
      <div className="space-y-2">
        <Pick title="Video or audio source" hint="MP4, MP3, WAV (max 500MB)" file={media} setFile={setMedia} accept=".mp4,.mp3,.wav,.m4a,.webm,.mov" inputRef={mRef} />
        <Pick title="Presentation slides" hint="PPTX or PDF for slide-sync (optional)" file={slides} setFile={setSlides} accept=".pptx,.pdf" inputRef={sRef} />
        <Notice>Files are processed in a temporary directory and deleted immediately after analysis.</Notice>
      </div>
      <div className="lbl mt-6 mb-2">03 · Audience parameters</div>
      <div className="grid md:grid-cols-3 gap-3">
        <div><div className="lbl mb-1">Session title</div><input className="inp" placeholder="e.g. Q3 Product Roadmap" value={title} onChange={(e) => setTitle(e.target.value)} /></div>
        <div><div className="lbl mb-1">Audience persona</div><select className="inp" value={persona} onChange={(e) => setPersona(e.target.value)}>{['Professor', 'Investor', 'Beginner', 'General'].map((p) => <option key={p}>{p}</option>)}</select></div>
        <div><div className="lbl mb-1">Spoken language</div><select className="inp" value={lang} onChange={(e) => setLang(e.target.value)}>{[['en-IN', 'English (India)'], ['hi-IN', 'Hindi'], ['ta-IN', 'Tamil'], ['te-IN', 'Telugu'], ['bn-IN', 'Bengali'], ['mr-IN', 'Marathi'], ['kn-IN', 'Kannada'], ['ml-IN', 'Malayalam'], ['gu-IN', 'Gujarati']].map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></div>
      </div>
      <div className="space-y-3 mt-4">
        <Toggle on={store} set={setStore} label="Store transcript for report" />
        <Toggle on={cv} set={setCv} label="Enable computer vision (eye-contact / posture)" />
        <Toggle on={qa} set={setQa} label="Simulated Q&A generation" />
      </div>
      {err && <div className="text-xs text-bad font-semibold mt-4">{err}</div>}
      <div className="mt-6 text-center"><button className="btn px-8" disabled={busy} onClick={start}>{busy ? 'Uploading…' : 'Start analysis pipeline'}</button></div>
      <div className="text-center text-[10px] text-gray-500 mt-3">Engagement metrics are indicators, not absolute judgments.</div>
    </Shell>
  )
}
