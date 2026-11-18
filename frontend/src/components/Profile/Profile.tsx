import { useEffect, useState } from 'react'
import { LockKeyhole, LogOut, ShieldCheck, UserRound } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getProfile } from '../../lib/api'

type Profile = { id: number; name: string; email: string }

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>()
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    getProfile().then(setProfile).catch(err => setError(err.message))
  }, [])

  function logout() {
    localStorage.removeItem('taxwise_access_token')
    navigate('/login')
  }

  const initials = profile?.name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'U'

  if (error) return <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">Unable to load your profile: {error}</p>
  if (!profile) return <p role="status" className="text-sm text-slate-500">Loading your profile...</p>

  return <div className="fade-in max-w-4xl space-y-8">
    <div><p className="text-xs font-bold uppercase tracking-[.18em] text-indigo-500">Account center</p><h2 className="mt-2 font-display text-3xl tracking-tight">Profile & settings</h2><p className="mt-2 text-slate-500">Account details from your TaxWise profile.</p></div>
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <aside className="surface rounded-2xl p-3">
        <div className="flex items-center gap-3 rounded-xl bg-indigo-50 p-3 text-sm font-bold text-indigo-700"><UserRound size={17}/> Personal information</div>
        <div className="mt-1 flex items-center gap-3 rounded-xl p-3 text-sm text-slate-500"><ShieldCheck size={17}/> Tax preferences</div>
        <div className="mt-1 flex items-center gap-3 rounded-xl p-3 text-sm text-slate-500"><LockKeyhole size={17}/> Security</div>
        <button type="button" onClick={logout} className="mt-6 flex w-full items-center gap-3 rounded-xl p-3 text-sm font-bold text-rose-600 hover:bg-rose-50"><LogOut size={17}/> Log out</button>
      </aside>
      <div className="space-y-6">
        <section className="surface rounded-2xl p-6">
          <div className="flex items-center gap-4 border-b border-slate-100 pb-6"><div className="grid h-16 w-16 place-items-center rounded-full bg-indigo-100 font-display text-xl text-indigo-700">{initials}</div><div><h3 className="font-display text-xl">{profile.name}</h3><p className="text-sm text-slate-500">{profile.email}</p></div><span className="ml-auto"><ShieldCheck className="text-emerald-500" size={21}/></span></div>
          <div className="grid gap-5 pt-6 sm:grid-cols-2">
            <label className="text-xs font-bold uppercase tracking-wide text-slate-500">Full name<input readOnly value={profile.name} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm font-medium text-slate-900 outline-none"/></label>
            <label className="text-xs font-bold uppercase tracking-wide text-slate-500">Email address<input readOnly value={profile.email} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm font-medium text-slate-900 outline-none"/></label>
          </div>
        </section>
        <section className="surface rounded-2xl p-6">
          <h3 className="font-display text-lg">Tax preferences</h3>
          <p className="mt-1 text-sm text-slate-500">Tax preferences are not currently saved to your account. Set the assessment year and financial inputs in Tax planning before calculating.</p>
        </section>
      </div>
    </div>
  </div>
}
