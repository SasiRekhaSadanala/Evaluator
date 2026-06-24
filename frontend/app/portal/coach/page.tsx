'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import StudentNavbar from '@/components/StudentNavbar'
import { AuthStore } from '@/lib/auth-store'
import { API_BASE } from '@/lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  streaming?: boolean
}

interface CoachStatus {
  available: boolean
  backend: string
  model: string
}

/* ------------------------------------------------------------------ */
/*  Suggested Prompts (just quick-start suggestions)                   */
/* ------------------------------------------------------------------ */

const SUGGESTED_PROMPTS = [
  { icon: 'trending_up', label: 'How can I improve my scores?', color: 'from-violet-500 to-violet-600' },
  { icon: 'psychology', label: 'What are my weakest areas?', color: 'from-amber-500 to-orange-500' },
  { icon: 'code', label: 'Tips to write cleaner code', color: 'from-rose-500 to-pink-500' },
  { icon: 'rate_review', label: 'Explain my last feedback in detail', color: 'from-cyan-500 to-blue-500' },
]

/* ------------------------------------------------------------------ */
/*  Markdown-like renderer (lightweight)                               */
/* ------------------------------------------------------------------ */

function renderMarkdown(text: string) {
  const lines = text.split('\n')
  const elements: JSX.Element[] = []

  lines.forEach((line, i) => {
    // Process inline formatting
    const processInline = (str: string, key: string): JSX.Element => {
      // Bold
      const parts = str.split(/\*\*(.*?)\*\*/g)
      if (parts.length > 1) {
        return (
          <span key={key}>
            {parts.map((part, j) =>
              j % 2 === 1 ? <strong key={j} className="font-semibold text-frost">{part}</strong> : processCode(part, `${key}-c${j}`)
            )}
          </span>
        )
      }
      return processCode(str, key)
    }

    const processCode = (str: string, key: string): JSX.Element => {
      const codeParts = str.split(/`([^`]+)`/g)
      if (codeParts.length > 1) {
        return (
          <span key={key}>
            {codeParts.map((part, j) =>
              j % 2 === 1 ? (
                <code key={j} className="px-1.5 py-0.5 bg-surface-container-highest/50 rounded text-violet-primary text-xs font-mono">{part}</code>
              ) : <span key={j}>{part}</span>
            )}
          </span>
        )
      }
      return <span key={key}>{str}</span>
    }

    // Checkboxes (study plan items)
    if (line.match(/^\s*-\s*\[\s*\]\s*/)) {
      const content = line.replace(/^\s*-\s*\[\s*\]\s*/, '')
      elements.push(
        <div key={i} className="flex gap-2 ml-4 my-0.5">
          <span className="text-violet-primary/50 mt-0.5">☐</span>
          <span className="flex-1">{processInline(content, `cb-${i}`)}</span>
        </div>
      )
      return
    }

    // Bullet points
    if (line.match(/^\s*[-•]\s+/)) {
      const content = line.replace(/^\s*[-•]\s+/, '')
      const indent = line.match(/^(\s*)/)?.[1]?.length || 0
      elements.push(
        <div key={i} className="flex gap-2 my-0.5" style={{ marginLeft: `${Math.max(8, indent * 4)}px` }}>
          <span className="text-violet-primary mt-0.5 text-xs">•</span>
          <span className="flex-1">{processInline(content, `b-${i}`)}</span>
        </div>
      )
      return
    }

    // Numbered lists
    if (/^\d+\.\s/.test(line)) {
      const num = line.match(/^(\d+)\./)?.[1]
      const content = line.replace(/^\d+\.\s/, '')
      elements.push(
        <div key={i} className="flex gap-2 ml-2 my-0.5">
          <span className="text-violet-primary text-xs font-mono w-4">{num}.</span>
          <span className="flex-1">{processInline(content, `n-${i}`)}</span>
        </div>
      )
      return
    }

    // Empty lines
    if (!line.trim()) {
      elements.push(<div key={i} className="h-2" />)
      return
    }

    elements.push(<div key={i} className="my-0.5">{processInline(line, `l-${i}`)}</div>)
  })

  return elements
}

/* ------------------------------------------------------------------ */
/*  Page Component                                                     */
/* ------------------------------------------------------------------ */

export default function AICoachPage() {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [status, setStatus] = useState<CoachStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [generatingPlan, setGeneratingPlan] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auth check
  useEffect(() => {
    const { isAuthenticated, user } = AuthStore.getState()
    if (!isAuthenticated || user?.role !== 'student') {
      router.push('/login')
      return
    }

    AuthStore.fetchAuth(`${API_BASE}/api/portal/chat/status`)
      .then(r => r.json())
      .then(d => setStatus(d))
      .catch(() => setStatus({ available: false, backend: 'none', model: '' }))
      .finally(() => setStatusLoading(false))
  }, [router])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Stream a response from an SSE endpoint
  const streamResponse = useCallback(async (url: string, body: object | null, userMsg?: Message) => {
    const assistantMsg: Message = {
      id: `a-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    }

    if (userMsg) {
      setMessages(prev => [...prev, userMsg, assistantMsg])
    } else {
      setMessages(prev => [...prev, assistantMsg])
    }
    setStreaming(true)

    try {
      const token = AuthStore.getState().token
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        ...(body ? { body: JSON.stringify(body) } : {}),
      })

      if (!response.ok) {
        const errText = response.status === 503
          ? '**Ollama is not running.** Start it with:\n\n`ollama serve`\n`ollama pull phi3:mini`\n\nThen refresh this page.'
          : `_Connection error (HTTP ${response.status}). Is the backend running?_`
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'assistant') {
            updated[updated.length - 1] = { ...last, streaming: false, content: errText }
          }
          return updated
        })
        return
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const jsonStr = line.slice(6).trim()
            if (!jsonStr) continue

            try {
              const parsed = JSON.parse(jsonStr)
              if (parsed.done) break
              if (parsed.token) {
                accumulated += parsed.token
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  if (last?.role === 'assistant') {
                    updated[updated.length - 1] = { ...last, content: accumulated }
                  }
                  return updated
                })
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }

      // Mark streaming complete
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'assistant') {
          updated[updated.length - 1] = {
            ...last,
            streaming: false,
            content: accumulated || '_No response received. Is Ollama running?_',
          }
        }
        return updated
      })
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'assistant') {
          updated[updated.length - 1] = {
            ...last,
            streaming: false,
            content: '**Cannot connect to AI Coach.** Make sure the backend is running:\n\n`python -m uvicorn backend.app.main:app`\n\nAnd Ollama is active:\n\n`ollama serve`',
          }
        }
        return updated
      })
    } finally {
      setStreaming(false)
      setGeneratingPlan(false)
      inputRef.current?.focus()
    }
  }, [])

  // Send a chat message
  const sendMessage = useCallback(async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || streaming) return

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: msg,
      timestamp: new Date(),
    }

    setInput('')

    const conversationHistory = messages.slice(-6).map(m => ({
      role: m.role,
      content: m.content,
    }))

    await streamResponse(
      `${API_BASE}/api/portal/chat`,
      { message: msg, conversation_history: conversationHistory },
      userMsg,
    )
  }, [input, streaming, messages, streamResponse])

  // Generate structured improvement plan
  const generatePlan = useCallback(async () => {
    if (streaming || generatingPlan) return
    setGeneratingPlan(true)

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: '📋 Generate my personalized improvement plan',
      timestamp: new Date(),
    }

    await streamResponse(
      `${API_BASE}/api/portal/improvement-plan`,
      {},
      userMsg,
    )
  }, [streaming, generatingPlan, streamResponse])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const { user } = AuthStore.getState()
  const displayName = user?.display_name?.split(' ')[1] || user?.display_name || 'Student'

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <StudentNavbar />

      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="px-6 py-5 border-b border-outline-variant/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-primary to-violet-container flex items-center justify-center shadow-violet-glow">
                <span className="material-symbols-outlined text-white text-xl">psychology</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-frost">AI Study Coach</h1>
                <div className="flex items-center gap-2">
                  {statusLoading ? (
                    <span className="text-xs text-frost-muted">Checking Ollama...</span>
                  ) : status?.available ? (
                    <>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-trust animate-pulse" />
                      <span className="text-xs text-frost-muted">
                        Powered by Phi-3 Mini (Local · Private · Offline)
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="w-1.5 h-1.5 rounded-full bg-coral" />
                      <span className="text-xs text-coral">Offline — run `ollama serve` to enable</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {messages.length > 0 && (
                <button
                  onClick={() => setMessages([])}
                  className="text-xs text-frost-muted hover:text-frost transition-colors px-3 py-1.5 rounded-lg hover:bg-surface-container-low"
                >
                  Clear Chat
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6" style={{ maxHeight: 'calc(100vh - 250px)' }}>
          {messages.length === 0 ? (
            /* Welcome State */
            <div className="flex flex-col items-center justify-center py-8 animate-fade-in">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-primary/20 to-violet-container/20 border border-violet-primary/10 flex items-center justify-center mb-6">
                <span className="material-symbols-outlined text-4xl text-violet-primary">auto_awesome</span>
              </div>
              <h2 className="text-xl font-bold text-frost mb-2">
                Hey {displayName}, I&apos;m your AI Study Coach
              </h2>
              <p className="text-sm text-frost-muted max-w-md text-center mb-3">
                I can answer <span className="text-violet-primary font-medium">any question</span> — academics, coding, career advice, or study strategies. I also know your scores and feedback for personalized guidance.
              </p>
              <p className="text-xs text-frost-muted/60 mb-8">
                Runs 100% locally on your machine via Phi-3 Mini · No data leaves your device
              </p>

              {/* Generate Plan CTA */}
              <button
                onClick={generatePlan}
                disabled={streaming || !status?.available}
                className="group mb-8 w-full max-w-lg flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-violet-primary/10 to-violet-container/10 border border-violet-primary/20 hover:border-violet-primary/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-primary to-violet-container flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-lg">
                  <span className="material-symbols-outlined text-white text-xl">assignment</span>
                </div>
                <div className="text-left">
                  <p className="text-sm font-semibold text-frost">Generate My Improvement Plan</p>
                  <p className="text-xs text-frost-muted">Get a structured, week-by-week study plan based on your actual scores and weak areas</p>
                </div>
                <span className="material-symbols-outlined text-violet-primary ml-auto text-lg">arrow_forward</span>
              </button>

              {/* Suggested prompts — quick starts, not the only options */}
              <p className="text-xs text-frost-muted/50 uppercase tracking-wider font-medium mb-3">or ask anything</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                {SUGGESTED_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(prompt.label)}
                    disabled={streaming || !status?.available}
                    className="group flex items-center gap-3 p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/10 hover:border-violet-primary/30 hover:bg-surface-container-highest/30 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${prompt.color} flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform`}>
                      <span className="material-symbols-outlined text-white text-sm">{prompt.icon}</span>
                    </div>
                    <span className="text-sm text-frost-muted group-hover:text-frost transition-colors">{prompt.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Message thread */
            messages.map(msg => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-primary to-violet-container flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                    <span className="material-symbols-outlined text-white text-sm">psychology</span>
                  </div>
                )}
                <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                    ? 'bg-violet-primary/90 text-white rounded-br-md'
                    : 'bg-surface-container-low border border-outline-variant/10 text-frost-muted rounded-bl-md'
                  }`}>
                  {msg.role === 'assistant' ? (
                    <div className="text-sm leading-relaxed">
                      {renderMarkdown(msg.content)}
                      {msg.streaming && (
                        <span className="inline-block w-2 h-4 bg-violet-primary/70 rounded-sm ml-0.5 animate-pulse" />
                      )}
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  )}
                  <p className={`text-[10px] mt-1.5 ${msg.role === 'user' ? 'text-white/50' : 'text-frost-muted/50'}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-xs font-bold text-frost">{displayName[0]?.toUpperCase()}</span>
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="px-6 pb-6 pt-2">
          <div className="relative bg-surface-container-low rounded-2xl border border-outline-variant/10 focus-within:border-violet-primary/30 transition-colors shadow-lg">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                status?.available
                  ? 'Ask anything — coding help, study tips, career advice...'
                  : 'Ollama offline — run: ollama serve'
              }
              disabled={streaming || !status?.available}
              rows={1}
              className="w-full bg-transparent text-frost text-sm px-5 py-4 pr-14 resize-none outline-none placeholder:text-frost-muted/40 disabled:opacity-50 max-h-32 overflow-y-auto"
              style={{ minHeight: '52px' }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || streaming || !status?.available}
              className="absolute right-3 bottom-3 w-9 h-9 rounded-xl bg-violet-primary hover:bg-violet-container disabled:bg-surface-container-highest disabled:text-frost-muted text-white flex items-center justify-center transition-all hover:scale-105 disabled:hover:scale-100"
            >
              {streaming ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <span className="material-symbols-outlined text-lg">send</span>
              )}
            </button>
          </div>
          <p className="text-[10px] text-frost-muted/40 text-center mt-2">
            Powered by Phi-3 Mini running locally · Your data never leaves your machine · Ask any question
          </p>
        </div>
      </div>

      {/* Background pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
    </div>
  )
}
