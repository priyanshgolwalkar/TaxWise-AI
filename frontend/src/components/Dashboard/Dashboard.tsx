import { useEffect, useState } from 'react'
import { Activity, ArrowRight, BarChart3, CheckCircle2, FileCheck2, FileText, Lightbulb, ReceiptIndianRupee, ShieldCheck, UploadCloud } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getDashboardSummary } from '../../lib/api'
import { EmptyState, Pill, Section, Skeleton, Stat } from '../UI'

const money = (value: number | null | undefined) => value == null ? '—' : `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function DashboardPage() {
  const [data, setData] = useState<any>()
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    setError('')
    getDashboardSummary().then(setData).catch(err => setError(err.message))
  }, [refresh])

  if (error) return <div role="alert" className="surface rounded-2xl p-8 text-sm text-rose-600">We couldn't load your overview. <button type="button" onClick={() => setRefresh(value => value + 1)} className="font-bold underline">Try again</button></div>
  if (!data) return <div className="space-y-6"><Skeleton className="h-10 w-72"/><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[1, 2, 3, 4].map(item => <Skeleton key={item} className="h-36"/>)}</div><Skeleton className="h-72"/></div>

  const summary = data.summary
  const comparison = data.latest_tax_calculation?.comparison
  const assessmentYear = data.latest_tax_calculation?.assessment_year
  const recommended = summary.recommended_regime
  const userName = data.user_profile?.name || 'there'

  return <div className="fade-in space-y-8">
    <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
      <div><p className="mb-2 text-xs font-bold uppercase tracking-[.18em] text-indigo-500">Tax planning workspace</p><h2 className="font-display text-3xl tracking-tight md:text-4xl">Welcome, {userName}</h2><p className="mt-2 text-slate-500">Here's your tax planning overview.</p></div>
      <div className="flex gap-2"><button type="button" onClick={() => setRefresh(value => value + 1)} className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-600 shadow-sm">Refresh</button><Link to="/tax" className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700">Review tax position <ArrowRight size={16}/></Link></div>
    </div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Stat label="Estimated tax" value={money(summary.estimated_tax)} meta={recommended ? `${recommended} regime · AY ${assessmentYear || '—'}` : 'Run a comparison first'} icon={ReceiptIndianRupee} accent="indigo"/>
      <Stat label="Recommended regime" value={recommended || '—'} meta="Based on latest comparison" icon={ShieldCheck} accent="blue"/>
      <Stat label="Potential savings" value={money(summary.potential_savings)} meta="Compared across regimes" icon={BarChart3} accent="violet"/>
      <Stat label="Documents" value={String(summary.total_documents)} meta={`${summary.documents_needing_verification} need verification`} icon={FileCheck2} accent="white"/>
    </div>
    <div className="grid gap-6 xl:grid-cols-[1.35fr_.9fr]">
      <Section title="Regime comparison">
        <div className="surface overflow-hidden rounded-2xl">{!comparison ? <EmptyState title="No tax comparison yet" detail="Add your verified financial inputs to compare old and new regimes." action={<Link to="/tax" className="inline-flex rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white">Calculate your tax</Link>}/> : <div className="p-6">
          <div className="mb-6 flex items-center justify-between"><div><p className="text-sm text-slate-500">Recommended regime</p><h3 className="mt-1 font-display text-2xl capitalize">{recommended} regime</h3></div><Pill tone="blue">Potentially lower tax</Pill></div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className={`rounded-xl border p-4 ${recommended === 'old' ? 'border-indigo-300 bg-indigo-50/60' : 'border-slate-200'}`}><div className="flex justify-between text-sm"><span className="font-semibold">Old regime</span><span className="font-bold">{money(summary.old_regime_tax)}</span></div><p className="mt-5 text-xs text-slate-500">Tax from latest saved calculation</p></div>
            <div className={`rounded-xl border p-4 ${recommended === 'new' ? 'border-indigo-300 bg-indigo-50/60' : 'border-slate-200'}`}><div className="flex justify-between text-sm"><span className="font-semibold">New regime</span><span className="font-bold">{money(summary.new_regime_tax)}</span></div><p className="mt-5 text-xs text-slate-500">Tax from latest saved calculation</p></div>
          </div>
          <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-sm text-slate-500"><CheckCircle2 size={16} className="text-emerald-500"/> Potential difference: <strong className="text-slate-900">{money(summary.potential_savings)}</strong></div>
        </div>}</div>
      </Section>
      <Section title="Tax-saving opportunities"><div className="surface space-y-1 rounded-2xl p-5">{data.recommendations?.items?.length ? data.recommendations.items.slice(0, 3).map((item: any) => <div key={item.title} className="flex gap-3 border-b border-slate-100 py-3 last:border-0"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-amber-50 text-amber-600"><Lightbulb size={17}/></div><div><p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs leading-5 text-slate-500">Potential impact {money(item.impact)}</p></div></div>) : <div className="p-3 text-sm text-slate-500">Run a tax comparison to see potentially applicable opportunities.</div>}</div></Section>
    </div>
    <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
      <Section title="Recent documents"><div className="surface rounded-2xl p-4">{data.document_summary.length ? data.document_summary.slice(0, 5).map((document: any) => <div key={document.id} className="flex items-center gap-3 border-b border-slate-100 py-3 last:border-0"><div className="grid h-9 w-9 place-items-center rounded-lg bg-indigo-50 text-indigo-600"><FileText size={16}/></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{document.filename}</p><p className="text-xs text-slate-500">{document.status}</p></div><Pill tone={document.status === 'needs_review' ? 'yellow' : 'green'}>{document.status.replace('_', ' ')}</Pill></div>) : <EmptyState title="No documents yet" detail="Upload Form 16 or investment proofs to begin." action={<Link to="/documents" className="inline-flex items-center gap-2 text-sm font-bold text-indigo-600">Upload document <UploadCloud size={15}/></Link>}/>}</div></Section>
      <Section title="Recent activity"><div className="surface rounded-2xl p-4">{data.recent_activity.length ? data.recent_activity.slice(0, 5).map((item: any) => <div key={`${item.type}-${item.record_id}`} className="flex gap-3 border-b border-slate-100 py-3 last:border-0"><div className="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 text-slate-500"><Activity size={16}/></div><div><p className="text-sm font-semibold">{item.label}</p><p className="text-xs text-slate-500">{item.type.replace('_', ' ')}</p></div></div>) : <div className="p-3 text-sm text-slate-500">Your recent activity will appear here.</div>}</div></Section>
    </div>
  </div>
}
