import { ChangeEvent, DragEvent, useEffect, useRef, useState } from 'react'
import { CheckCircle2, Eye, FileImage, FileText, UploadCloud, X } from 'lucide-react'
import { listDocuments, uploadDocument } from '../../lib/api'
import { EmptyState, Pill, Section, Skeleton } from '../UI'

type ExtractedField = { value: string | null; confidence: string; needs_review: boolean }
type DocumentItem = {
  id: number
  filename: string
  content_type: string
  size_bytes: number
  status: string
  extracted_data?: {
    fields?: Record<string, ExtractedField>
    missing_fields?: string[]
    validation_errors?: string[]
    requires_user_verification?: boolean
  }
}

const statusTone = (status: string) => status === 'needs_review' ? 'yellow' : status === 'processing' ? 'blue' : status === 'failed' ? 'red' : 'green'

export default function DocumentsPage() {
  const input = useRef<HTMLInputElement>(null)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selected, setSelected] = useState<DocumentItem>()
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listDocuments().then(items => setDocuments(items as DocumentItem[])).catch(err => setError(err.message)).finally(() => setLoading(false))
  }, [])

  async function handleFile(file?: File) {
    if (!file) return
    setError('')
    setMessage('')
    if (!['application/pdf', 'image/png', 'image/jpeg'].includes(file.type)) {
      setError('Please choose a PDF, PNG, or JPEG file.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Files must be 10 MB or smaller.')
      return
    }
    setBusy(true)
    try {
      const document = await uploadDocument(file) as DocumentItem
      setDocuments(current => [document, ...current])
      setMessage('Document uploaded. OCR results are ready for your verification.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  function select(event: ChangeEvent<HTMLInputElement>) {
    void handleFile(event.target.files?.[0])
    event.target.value = ''
  }

  function drop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault()
    setDragging(false)
    void handleFile(event.dataTransfer.files?.[0])
  }

  return <div className="fade-in space-y-8">
    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-xs font-bold uppercase tracking-[.18em] text-indigo-500">Secure workspace</p><h2 className="mt-2 font-display text-3xl tracking-tight">Your documents</h2><p className="mt-2 text-slate-500">Upload the source documents behind your tax picture.</p></div><div className="flex items-center gap-2 text-xs text-slate-500"><CheckCircle2 size={15} className="text-emerald-500"/> OCR output always needs review</div></div>
    <input ref={input} onChange={select} type="file" accept="application/pdf,image/png,image/jpeg" className="hidden"/>
    <button type="button" disabled={busy} onClick={() => input.current?.click()} onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={drop} className={`w-full rounded-2xl border-2 border-dashed p-10 text-center transition ${dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-indigo-50/30'} disabled:opacity-60`}>
      <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-indigo-50 text-indigo-600"><UploadCloud size={25}/></div><h3 className="mt-4 font-display text-lg">{busy ? 'Processing document...' : 'Drop a file here or browse'}</h3><p className="mt-2 text-sm text-slate-500">Form 16, salary slips, and investment proofs</p><p className="mt-3 text-xs text-slate-400">PDF, PNG, or JPEG · Maximum 10 MB</p>
    </button>
    {message && <p role="status" className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p>}
    {error && <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
    <Section title="Document library" action={documents.length ? `${documents.length} files` : undefined}>
      {loading ? <div className="surface space-y-3 rounded-2xl p-5"><Skeleton className="h-14"/><Skeleton className="h-14"/></div> : documents.length === 0 ? <EmptyState title="Your library is empty" detail="Upload a document to start extracting financial data for review."/> : <div className="surface overflow-hidden rounded-2xl">
        <div className="hidden grid-cols-[1.5fr_1fr_1fr_auto] gap-4 border-b border-slate-100 bg-slate-50 px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-slate-400 md:grid"><span>Document</span><span>Type</span><span>Status</span><span/></div>
        {documents.map(document => <div key={document.id} className="grid gap-3 border-b border-slate-100 px-5 py-4 last:border-0 md:grid-cols-[1.5fr_1fr_1fr_auto] md:items-center md:gap-4">
          <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-50 text-indigo-600">{document.content_type === 'application/pdf' ? <FileText size={18}/> : <FileImage size={18}/>}</div><div className="min-w-0"><p className="truncate text-sm font-semibold">{document.filename}</p><p className="text-xs text-slate-500">{(document.size_bytes / 1024).toFixed(0)} KB</p></div></div>
          <span className="text-xs capitalize text-slate-500">{document.content_type.split('/')[1]}</span>
          <div><Pill tone={statusTone(document.status)}>{document.status.replace('_', ' ')}</Pill><p className="mt-1 text-[11px] text-slate-400">{document.extracted_data?.missing_fields?.length ? 'Verification needed' : 'OCR complete'}</p></div>
          <button type="button" onClick={() => setSelected(document)} className="flex w-fit items-center gap-1 text-xs font-bold text-indigo-600"><Eye size={14}/> View data</button>
        </div>)}
      </div>}
    </Section>
    {selected && <div className="fixed inset-0 z-40 grid place-items-center bg-slate-950/40 p-4" onClick={() => setSelected(undefined)}>
      <section role="dialog" aria-modal="true" aria-labelledby="document-details-title" className="surface max-h-[85vh] w-full max-w-2xl overflow-auto rounded-2xl p-6" onClick={event => event.stopPropagation()}>
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-widest text-indigo-500">OCR review</p><h2 id="document-details-title" className="mt-2 font-display text-xl">{selected.filename}</h2></div><button type="button" aria-label="Close document details" onClick={() => setSelected(undefined)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={18}/></button></div>
        <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">{selected.extracted_data?.requires_user_verification ? 'OCR values are unverified and are not used in tax calculations.' : 'Review extracted values before using them.'}</p>
        {selected.extracted_data?.fields && <div className="mt-5 space-y-2">{Object.entries(selected.extracted_data.fields).map(([field, value]) => <div key={field} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 p-3"><div><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{field.replace(/_/g, ' ')}</p><p className="mt-1 text-sm font-semibold">{value.value ?? 'Not detected'}</p></div><Pill tone={value.needs_review ? 'yellow' : 'green'}>{value.needs_review ? 'Needs review' : value.confidence}</Pill></div>)}</div>}
        {!!selected.extracted_data?.missing_fields?.length && <p className="mt-4 text-sm text-slate-600">Missing fields: {selected.extracted_data.missing_fields.join(', ')}</p>}
        {!!selected.extracted_data?.validation_errors?.length && <ul className="mt-3 list-disc pl-5 text-sm text-rose-700">{selected.extracted_data.validation_errors.map(issue => <li key={issue}>{issue}</li>)}</ul>}
        <p className="mt-5 text-xs leading-5 text-slate-500">Field verification and editing are not available yet. Check the original document and enter confirmed values on the Tax planning page.</p>
      </section>
    </div>}
  </div>
}
