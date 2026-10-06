import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearAuth, getUser } from '../api'
import { Shell, Notice, useLogout } from '../ui'

export default function Settings() {
  const u = getUser(), nav = useNavigate(), logout = useLogout()
  const [msg, setMsg] = useState('')
  async function wipe(account) {
    if (!confirm(account ? 'Delete your account and ALL data permanently?' : 'Delete all your sessions and reports permanently?')) return
    await api(`/me/data?delete_account=${account}`, { method: 'DELETE' })
    if (account) { clearAuth(); nav('/') } else setMsg('All your analysis data was deleted.')
  }
  return (
    <Shell>
      <div className="lbl">Account</div><h1 className="text-2xl font-extrabold">Settings</h1>
      <div className="card p-4 mt-4"><div className="lbl">Signed in as</div><div className="font-bold">{u?.name} · {u?.email}</div><button className="btn2 mt-3" onClick={logout}>Log out</button></div>
      <div className="card p-4 mt-4"><div className="lbl">Privacy & data</div>
        <p className="text-sm text-gray-600 mt-2">Videos, audio and slides are never stored: they are deleted right after analysis. Only scores, metrics, suggestions and Q&A are saved. Transcripts are saved only if you opt in.</p>
        <div className="flex flex-wrap gap-2 mt-3"><button className="btn2 text-bad" onClick={() => wipe(false)}>Delete my data</button><button className="btn2 text-bad" onClick={() => wipe(true)}>Delete my account</button></div>
        {msg && <div className="text-xs text-ok font-semibold mt-2">{msg}</div>}</div>
      <div className="mt-4"><Notice>Eye-contact and engagement metrics are indicators, not absolute judgments, and may vary across cultures and disabilities.</Notice></div>
    </Shell>
  )
}
