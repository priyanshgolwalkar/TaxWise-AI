import { useEffect, useState } from 'react'
import { NavLink, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Bell, ChevronDown, FileText, LayoutDashboard, Lightbulb, LogOut, Menu, MessageCircle, ReceiptIndianRupee, Settings, UploadCloud, UserRound, X } from 'lucide-react'
import { getProfile, getToken } from '../lib/api'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/documents', label: 'Documents', icon: UploadCloud },
  { to: '/tax', label: 'Tax planning', icon: ReceiptIndianRupee },
  { to: '/recommendations', label: 'Recommendations', icon: Lightbulb },
  { to: '/assistant', label: 'AI assistant', icon: MessageCircle },
  { to: '/reports', label: 'Reports', icon: FileText },
]

export default function Layout() {
  const [open, setOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [profile, setProfile] = useState<{ name: string; email: string }>()
  const [profileError, setProfileError] = useState('')
  const location = useLocation()
  const navigate = useNavigate()
  const current = links.find(link => link.to === location.pathname)?.label || 'Profile'
  const initials = profile?.name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'U'

  useEffect(() => {
    if (!getToken()) return
    getProfile().then(setProfile).catch(err => setProfileError(err.message))
  }, [])

  if (!getToken()) return <Navigate to="/login" replace/>

  function logout() {
    localStorage.removeItem('taxwise_access_token')
    navigate('/login')
  }

  return <div className="min-h-screen bg-[#f6f8fc] text-slate-900 md:flex">
    <aside className={`${open ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-30 flex w-[272px] flex-col border-r border-white/10 bg-[#101a35] p-5 text-white transition-transform md:static md:translate-x-0`}>
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2.5 font-display text-xl tracking-tight"><span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-500 text-lg text-white shadow-lg shadow-indigo-900/30">T</span><span>TaxWise <span className="text-indigo-300">AI</span></span></div>
        <button type="button" className="md:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={19}/></button>
      </div>
      <p className="mb-8 mt-2 px-2 text-xs text-slate-400">Intelligent tax planning</p>
      <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-500">Workspace</p>
      <nav className="space-y-1">{links.map(({ to, label, icon: Icon }) => <NavLink onClick={() => setOpen(false)} key={to} to={to} className={({ isActive }) => `group flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium ${isActive ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-950/20' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}><Icon size={18} className="shrink-0"/>{label}</NavLink>)}</nav>
      <div className="mt-auto space-y-1 border-t border-white/10 pt-5">
        <NavLink to="/profile" className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-slate-400 hover:bg-white/5 hover:text-white"><UserRound size={18}/> Profile</NavLink>
        <button type="button" onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-slate-400 hover:bg-white/5 hover:text-white"><LogOut size={18}/> Logout</button>
        <div className="mt-4 flex items-center gap-3 rounded-xl bg-white/5 p-3"><div className="grid h-9 w-9 place-items-center rounded-full bg-indigo-400 text-xs font-bold">{initials}</div><div className="min-w-0"><p className="truncate text-sm font-semibold">{profile?.name || 'Loading account...'}</p><p className="truncate text-xs text-slate-500">{profile?.email || ' '}</p></div><Settings size={16} className="ml-auto text-slate-500"/></div>
      </div>
    </aside>
    {open && <button type="button" aria-label="Close navigation overlay" onClick={() => setOpen(false)} className="fixed inset-0 z-20 bg-slate-950/40 md:hidden"/>}
    <main className="min-w-0 flex-1">
      <header className="sticky top-0 z-10 flex h-[76px] items-center justify-between border-b border-slate-200/80 bg-[#f6f8fc]/90 px-5 backdrop-blur-xl md:px-10">
        <div className="flex items-center gap-3"><button type="button" onClick={() => setOpen(true)} className="rounded-lg p-2 text-slate-600 hover:bg-white md:hidden" aria-label="Open navigation"><Menu size={21}/></button><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-slate-400">Workspace</p><h1 className="font-display text-xl tracking-tight">{current}</h1></div></div>
        <div className="flex items-center gap-3">
          <button type="button" disabled title="Notifications are not available" className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-400 shadow-sm" aria-label="Notifications (not available)"><Bell size={18}/></button>
          <div className="relative">
            <button type="button" onClick={() => setProfileOpen(!profileOpen)} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white py-1.5 pl-1.5 pr-2.5 shadow-sm"><span className="grid h-8 w-8 place-items-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">{initials}</span><span className="hidden text-sm font-semibold sm:block">{profile?.name || 'Account'}</span><ChevronDown size={15} className="text-slate-400"/></button>
            {profileOpen && <div className="absolute right-0 mt-2 w-48 rounded-xl border border-slate-200 bg-white p-2 text-sm shadow-xl"><button type="button" onClick={() => navigate('/profile')} className="w-full rounded-lg px-3 py-2 text-left hover:bg-slate-50">Account settings</button><button type="button" onClick={logout} className="w-full rounded-lg px-3 py-2 text-left text-rose-600 hover:bg-rose-50">Sign out</button></div>}
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-[1480px] p-5 md:p-8 lg:p-10">
        {profileError && <p role="alert" className="mb-5 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">Unable to load your account profile: {profileError}</p>}
        <Outlet/>
      </div>
    </main>
  </div>
}
