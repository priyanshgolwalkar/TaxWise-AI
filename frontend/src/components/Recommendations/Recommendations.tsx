import { useEffect, useState } from 'react'
import { ArrowUpRight, CheckCircle2, Lightbulb, ShieldCheck } from 'lucide-react'
import { createRecommendations, getLatestRecommendations, getLatestTax, TaxInput } from '../../lib/api'
import { EmptyState, Pill, Section, Skeleton, Stat } from '../UI'

type TaxRecord = {
  input_data: TaxInput
  comparison: {
    recommended_regime: 'old' | 'new'
    estimated_savings: number
    old_regime: { final_liability: number }
    new_regime: { final_liability: number }
  }
}

type RecommendationItem = {
  title: string
  impact: number
  reason: string
}

type RecommendationResult = {
  regime: string
  items: RecommendationItem[]
}

const money = (value: number) => `₹${(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

function matchesCalculation(record: any, tax: TaxRecord) {
  return record.regime === tax.comparison.recommended_regime &&
    Object.entries(tax.input_data).every(([key, value]) => record.input_data?.[key] === value)
}

export default function RecommendationsPage() {
  const [tax, setTax] = useState<TaxRecord>()
  const [result, setResult] = useState<RecommendationResult>()
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getLatestTax(), getLatestRecommendations()])
      .then(([taxRecord, recommendationRecord]) => {
        if (!taxRecord) return
        setTax(taxRecord)
        if (recommendationRecord && matchesCalculation(recommendationRecord, taxRecord)) {
          setResult(recommendationRecord.recommendations)
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function generate() {
    if (!tax || generating) return
    setError('')
    setGenerating(true)
    try {
      const generated = await createRecommendations({
        ...tax.input_data,
        regime: tax.comparison.recommended_regime,
        tax_result: tax.comparison,
      })
      setResult(generated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate recommendations')
    } finally {
      setGenerating(false)
    }
  }

  if (error) return <div role="alert" className="surface rounded-2xl p-8 text-sm text-rose-600">We couldn't load recommendations. {error}</div>
  if (loading) return <div className="space-y-6"><Skeleton className="h-10 w-72"/><div className="grid gap-4 md:grid-cols-3"><Skeleton className="h-32"/><Skeleton className="h-32"/><Skeleton className="h-32"/></div><Skeleton className="h-48"/></div>
  if (!tax) return <div><h2 className="font-display text-3xl">Recommendations</h2><p className="mt-2 text-slate-500">Your explainable tax-saving workspace.</p><div className="mt-8"><EmptyState title="No tax position yet" detail="Run a regime comparison first. Recommendations will be based on that saved calculation."/></div></div>

  const comparison = tax.comparison
  const recommended = comparison.recommended_regime
  const liability = comparison[`${recommended}_regime`].final_liability

  return <div className="fade-in space-y-8">
    <div><p className="text-xs font-bold uppercase tracking-[.18em] text-indigo-500">Explainable planning</p><h2 className="mt-2 font-display text-3xl tracking-tight">Tax-saving opportunities</h2><p className="mt-2 text-slate-500">Potentially applicable ideas based on your current regime and inputs.</p></div>
    <div className="grid gap-4 md:grid-cols-3">
      <Stat label="Current tax position" value={money(liability)} meta={`${recommended} regime liability`} icon={ShieldCheck} accent="indigo"/>
      <Stat label="Recommended regime" value={`${recommended} regime`} meta="Based on lower configured liability" icon={CheckCircle2} accent="blue"/>
      <Stat label="Potential tax saving" value={money(comparison.estimated_savings)} meta="Not a guaranteed benefit" icon={Lightbulb} accent="violet"/>
    </div>
    <Section title="Potentially applicable opportunities">
      {!result ? <div className="surface rounded-2xl p-6">
        <p className="text-sm text-slate-500">Generate and save explainable recommendations for your latest tax calculation.</p>
        <button type="button" disabled={generating} onClick={generate} className="mt-4 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 disabled:opacity-60">{generating ? 'Generating...' : 'Generate recommendations'}</button>
      </div> : result.items.length === 0 ? <EmptyState title="No additional opportunities" detail="No rule-based opportunities were found for this selected regime."/> : <div className="grid gap-4 lg:grid-cols-2">
        {result.items.map((item, index) => <article key={item.title} className="surface rounded-2xl p-6">
          <div className="flex items-start justify-between gap-4"><div className="flex gap-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Lightbulb size={19}/></div><div><div className="flex flex-wrap items-center gap-2"><h3 className="font-display text-lg">{item.title}</h3><Pill tone="yellow">Potentially applicable</Pill></div><p className="mt-1 text-xs font-bold uppercase tracking-widest text-slate-400">Priority {index === 0 ? 'High' : 'Review'}</p></div></div><ArrowUpRight size={18} className="text-slate-300"/></div>
          <div className="mt-5 grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-4 text-sm"><div><p className="text-xs text-slate-500">Potential tax saving</p><p className="mt-1 font-bold">{money(item.impact)}</p></div><div><p className="text-xs text-slate-500">Applicable regime</p><p className="mt-1 font-bold capitalize">{result.regime}</p></div></div>
          <p className="mt-4 text-sm leading-6 text-slate-600"><strong className="text-slate-900">Why it applies:</strong> {item.reason}</p>
          <p className="mt-3 flex items-start gap-2 text-xs leading-5 text-slate-400"><ShieldCheck size={14} className="mt-0.5 shrink-0"/> Verify eligibility and supporting documents before acting.</p>
        </article>)}
      </div>}
    </Section>
  </div>
}
