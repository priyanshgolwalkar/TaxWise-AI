import { FormEvent, useEffect, useState } from 'react'
import { Bot, Check, Clipboard, Plus, Send, Sparkles, UserRound } from 'lucide-react'
import { createAssistantConversation, getAssistantMessages, listAssistantConversations, sendAssistantMessage } from '../../lib/api'

const suggestions = ['Which tax regime is better for me?', 'Explain my tax calculation', 'Why was this regime recommended?', 'What tax-saving opportunities are available to me?', 'What information is missing from my documents?']
type ChatMessage = { id?: number; role: 'assistant' | 'user'; content: string }

export default function AssistantPage() {
  const [conversations, setConversations] = useState<any[]>([])
  const [conversationId, setConversationId] = useState<string>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { listAssistantConversations().then(setConversations).catch(err => setError(err.message)).finally(() => setLoading(false)) }, [])

  async function openConversation(id: string) {
    setError(''); setConversationId(id); setLoading(true)
    try { setMessages(await getAssistantMessages(id)) } catch (err) { setError(err instanceof Error ? err.message : 'Unable to load conversation') }
    finally { setLoading(false) }
  }

  async function newConversation() {
    setError(''); setMessages([]); setLoading(true)
    try { const created = await createAssistantConversation(); setConversationId(created.id); setConversations(items => [created, ...items]) }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to create conversation') }
    finally { setLoading(false) }
  }

  async function send(text = message) {
    if (!text.trim() || sending) return
    setError(''); setSending(true)
    const submitted = text.trim()
    setMessages(items => [...items, { role: 'user', content: submitted }]); setMessage('')
    try {
      const response = await sendAssistantMessage(submitted, conversationId)
      setConversationId(response.conversation_id)
      setMessages(items => [...items, { role: 'assistant', content: response.answer }])
      const updated = await listAssistantConversations(); setConversations(updated)
    } catch (err) {
      setMessages(items => items.filter((item, index) => !(item.role === 'user' && index === items.length - 1 && item.content === submitted)))
      setMessage(submitted)
      setError(err instanceof Error ? err.message : 'Unable to send message')
    } finally { setSending(false) }
  }

  return <div className="fade-in grid gap-6 xl:grid-cols-[240px_1fr]">
    <aside className="surface hidden rounded-2xl p-4 xl:block"><div className="flex items-center justify-between"><p className="text-xs font-bold uppercase tracking-widest text-slate-400">Conversations</p><button type="button" onClick={newConversation} className="rounded-lg p-2 text-indigo-600 hover:bg-indigo-50" aria-label="New conversation"><Plus size={16}/></button></div><div className="mt-4 space-y-1">{conversations.map(item=><button type="button" onClick={()=>openConversation(item.id)} key={item.id} className={`w-full truncate rounded-xl p-3 text-left text-sm ${conversationId===item.id?'bg-indigo-50 font-semibold text-indigo-700':'text-slate-600 hover:bg-slate-50'}`}>{item.title||'New conversation'}</button>)}</div>{!conversations.length&&!loading&&<p className="mt-5 text-xs leading-5 text-slate-400">Your saved conversations will appear here.</p>}</aside>
    <section className="surface flex min-h-[640px] flex-col overflow-hidden rounded-2xl"><div className="flex items-center gap-3 border-b border-slate-100 p-5"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-200"><Bot size={21}/></div><div><h2 className="font-display text-lg">TaxWise guide</h2><p className="text-xs text-slate-500">Explanations grounded in your saved planning data</p></div><button type="button" onClick={newConversation} className="ml-auto flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:border-indigo-300 hover:text-indigo-600"><Plus size={14}/> New chat</button></div>
      <div className="flex-1 space-y-5 overflow-auto bg-slate-50/60 p-5 md:p-8">{!messages.length&&!loading&&<div className="mx-auto max-w-lg py-10 text-center"><div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-indigo-100 text-indigo-600"><Sparkles size={22}/></div><h3 className="mt-4 font-display text-xl">What would you like to understand?</h3><p className="mt-2 text-sm text-slate-500">Ask about your saved calculation, recommendations, or document review status.</p></div>}{messages.map((item,index)=><div key={item.id??`${item.role}-${index}`} className={`flex max-w-2xl gap-3 ${item.role==='user'?'ml-auto flex-row-reverse':''}`}><div className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${item.role==='assistant'?'bg-indigo-100 text-indigo-700':'bg-slate-200 text-slate-600'}`}>{item.role==='assistant'?<Sparkles size={15}/>:<UserRound size={15}/>}</div><div className={`rounded-2xl p-4 text-sm leading-6 ${item.role==='assistant'?'rounded-tl-sm bg-white text-slate-600 shadow-sm':'rounded-tr-sm bg-indigo-600 text-white'}`}>{item.content}{item.role==='assistant'&&<button type="button" onClick={()=>navigator.clipboard.writeText(item.content)} className="mt-3 flex items-center gap-1 text-xs font-bold text-indigo-600"><Clipboard size={13}/> Copy response</button>}</div></div>)}{sending&&<div className="flex items-center gap-3 text-sm text-slate-500"><div className="grid h-8 w-8 place-items-center rounded-full bg-indigo-100 text-indigo-700"><Sparkles size={15}/></div><span className="animate-pulse">TaxWise is preparing an explanation...</span></div>}{loading&&<p className="text-center text-xs text-slate-400">Loading conversation...</p>}</div>
      <div className="border-t border-slate-100 bg-white p-4"><p className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-400">Suggested questions</p><div className="mb-4 flex gap-2 overflow-x-auto pb-1">{suggestions.map(prompt=><button type="button" onClick={()=>send(prompt)} key={prompt} className="whitespace-nowrap rounded-full border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700">{prompt}</button>)}</div>{error&&<p role="alert" className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>}<form onSubmit={(event:FormEvent)=>{event.preventDefault();void send()}} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-2 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50"><input value={message} onChange={event=>setMessage(event.target.value)} placeholder="Ask about your tax planning..." className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none"/><button type="submit" disabled={sending||!message.trim()} className="grid h-10 w-10 place-items-center rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50" aria-label="Send message"><Send size={16}/></button></form><p className="mt-3 flex items-center gap-1 text-[11px] text-slate-400"><Check size={13}/> TaxWise explains deterministic results; verify complex decisions with a professional.</p></div></section>
  </div>
}
