import { useState } from 'react'
import { ArrowRight, CheckCircle2, CircleDollarSign, Info, ReceiptIndianRupee } from 'lucide-react'
import { compareTax, TaxInput } from '../../lib/api'
import { Pill, Section, Skeleton, Stat } from '../UI'

const initial: TaxInput = {
  assessment_year: '2025-26',
  annual_income: 0,
  deductions_80c: 0,
  deductions_80d: 0,
  home_loan_interest: 0,
  hra_exemption: 0,
}

const money = (value: number) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function TaxPage() {
  const [input, setInput] = useState(initial)
  const [result, setResult] = useState<any>()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const update = (key: keyof TaxInput) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setInput(current => ({ ...current, [key]: key === 'assessment_year' ? event.target.value : Number(event.target.value) }))

  async function calculate(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccess(false)
    try {
      setResult(await compareTax(input))
      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed')
    } finally {
      setBusy(false)
    }
  }

  const fields: [keyof TaxInput, string][] = [
    ['annual_income', 'Annual income'],
    ['deductions_80c', 'Section 80C'],
    ['deductions_80d', 'Section 80D'],
    ['home_loan_interest', 'Home loan interest'],
    ['hra_exemption', 'HRA exemption'],
  ]

  return <div className="fade-in space-y-8">
    <div><p className="text-xs font-bold uppercase tracking-[.18em] text-indigo-500">Planning workspace</p><h2 className="mt-2 font-display text-3xl tracking-tight">Tax planning</h2><p className="mt-2 text-slate-500">Compare regimes using your financial inputs. Verify all amounts before calculating.</p></div>
    <form onSubmit={calculate} className="surface rounded-2xl p-6">
      <div className="mb-6 flex items-start justify-between"><div><h3 className="font-display text-lg">Financial inputs</h3><p className="mt-1 text-sm text-slate-500">Values are sent to the deterministic tax engine.</p></div><div className="flex items-center gap-2 text-xs text-slate-500"><Info size={14}/> AY {input.assessment_year}</div></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{fields.map(([key, label]) => <label key={key} className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}<input min="0" type="number" value={input[key]} onChange={update(key)} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm font-medium text-slate-900 outline-none transition focus:border-indigo-400 focus:bg-white focus:ring-4 focus:ring-indigo-50"/></label>)}</div>
      <p className="mt-4 text-xs leading-5 text-slate-500">Standard deduction is selected by the configured tax rules for each regime; it is not an editable input.</p>
      <button type="submit" disabled={busy} className="mt-6 flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 disabled:opacity-60">{busy ? 'Calculating...' : 'Compare regimes'}<ArrowRight size={16}/></button>
    </form>
    {error && <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
    {success && <p role="status" className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">Calculation saved to your planning history.</p>}
    {busy ? <div className="grid gap-4 md:grid-cols-3"><Skeleton className="h-32"/><Skeleton className="h-32"/><Skeleton className="h-32"/></div> : result && <>
      <div className="grid gap-4 md:grid-cols-3"><Stat label="Recommended regime" value={`${result.recommended_regime} regime`} meta="Potentially lower liability" icon={CheckCircle2} accent="indigo"/><Stat label="Potential difference" value={money(result.estimated_savings)} meta="Across both configured regimes" icon={CircleDollarSign} accent="blue"/><Stat label="Assessment year" value={input.assessment_year} meta="Ruleset used for calculation" icon={ReceiptIndianRupee} accent="violet"/></div>
      <Section title="Old vs new regime"><div className="grid gap-5 lg:grid-cols-2">{[result.old_regime, result.new_regime].map((regime: any) => <div key={regime.regime} className={`surface rounded-2xl p-6 ${result.recommended_regime === regime.regime ? 'border-indigo-300 ring-4 ring-indigo-50' : ''}`}><div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-slate-400">{regime.regime} regime</p><p className="mt-2 font-display text-3xl">{money(regime.final_liability)}</p></div>{result.recommended_regime === regime.regime && <Pill tone="blue">Recommended</Pill>}</div><div className="mt-6 space-y-3 border-t border-slate-100 pt-5 text-sm"><div className="flex justify-between"><span className="text-slate-500">Taxable income</span><strong>{money(regime.taxable_income)}</strong></div><div className="flex justify-between"><span className="text-slate-500">Applicable deductions</span><strong>{money(regime.deductions)}</strong></div><div className="flex justify-between"><span className="text-slate-500">Rebate</span><strong>{money(regime.rebate)}</strong></div><div className="flex justify-between"><span className="text-slate-500">Cess</span><strong>{money(regime.cess)}</strong></div></div></div>)}</div></Section>
    </>}
  </div>
}
